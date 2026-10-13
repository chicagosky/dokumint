from MySQLdb import IntegrityError
import boto3, logging, os
from io import BytesIO 
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import File
from django.db import transaction
from django.utils.crypto import get_random_string
from jsonpath_ng.ext import parse

from cloudpathlib import CloudPath, S3Path
from core.exceptions import InvalidDocumentType
from core.models import Document, DocumentType, DocumentSubType
from core.models import Creator
from core.processors.cloud_processors import DocumentProcessorAbstractClass
from core.processors.response.parsers.expense_parser import ExpenseParser
from core.utils import get_app_setting

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

# DocumentType stores method names. Only these implementations may run.
_ANALYZE_METHODS = {
    'EXP': '_analyze_expense',
}
_SAVE_METHODS = {
    'EXP': '_save_expense',
}

class AWSProcessor(DocumentProcessorAbstractClass):
    """
    Implementation of DocumentProcessorAbstractClass for AWS
    """
    storage_prefix = 's3://'

    def create_storage(self, bucket_name: str, **kwargs):
        """
        Create an S3 bucket in a specified region

        :param bucket_name: Bucket to create
        :return: bucket name if created
        """
        _region_name = get_app_setting('', 'aws.region')
        s3_client = boto3.client('s3', region_name=_region_name)
        s3_client.create_bucket(
            Bucket=bucket_name, 
            CreateBucketConfiguration={
                'LocationConstraint': _region_name
            }
        )
        return bucket_name
    
    def create_folder(self, bucket_name: str, folder_names: list[str], **kwargs):
        """
        Create a folder within a S3 bucket 

        :param bucket_name: Bucket where the folder will be created
        :param folder_name: Folder name to be created
        :return: False if folder not created
        """
        _region_name = get_app_setting('', 'aws.region')
        s3_client = boto3.client('s3', region_name=_region_name)
        for folder_name in folder_names:
            s3_client.put_object(
                Bucket=bucket_name, 
                Body='',
                Key=folder_name
            )
        return folder_names
            
    
    def upload_document(self, file: File, file_ext: str, bucket_name: str, **kwargs):
        """
        Upload a file to an AWS S3 bucket

        :param file: File to upload
        :param file_ext: Extension of file being uploaded
        :param bucket_name: Bucket to upload to
        :return: Uploaded file name if file was uploaded, else False
        """
        # Random generated file name
        _file_key = get_app_setting('', 'cloud_processor.folders.documents') \
             + get_random_string(length=12) + file_ext
        s3_uri = self.storage_prefix + bucket_name + '/' + _file_key
        
        _region_name = get_app_setting('', 'aws.region')
        s3_client = boto3.client('s3', region_name=_region_name)
        try:
            # Convert in-memory user uploaded file into a byte stream for upload to S3
            b = file if type(file) is BytesIO else BytesIO(file.read())
            s3_client.upload_fileobj(b, bucket_name, _file_key)
        except ClientError as e:
            logger.error('Error uploading document::[bucket_name=%s]::[upload_file_key=%s]',bucket_name,_file_key)
            logger.exception(e)
            return False
        
        logger.info('EXIT::[bucket_name=%s]::[upload_file_location=%s]',bucket_name, s3_uri)
        return s3_uri
    

    def download_document_to_stream(self, file_name: str, bucket_name: str, stream_obj: BytesIO, **kwargs):
        """Download file from AWS S3 bucket to byte stream

        :param file_name: File to download
        :param bucket_name: Bucket hosting the file
        :param stream_obj: BytesIO stream representing the downloaded file
        :return: Byte stream representing file if successful, False if not successful
        """
        logger.info('ENTER::[file_name=%s]::[bucket_name=%s]',file_name, bucket_name)
        s3_client = boto3.client('s3')
        try:
            s3_client.download_fileobj(bucket_name, file_name, stream_obj)    
        except ClientError as e:
            logger.error('Error downloading receipt image:[file_name=%s]::[bucket_name=%s]', file_name, bucket_name)
            logger.exception(e)
            return False
        
        logger.info('EXIT::[file_name=%s]::[bucket_name=%s]',file_name, bucket_name)
        stream_obj.seek(0)
        return stream_obj
    
    def classify_document(self, path:str, **kwargs):
        """
        Extracting relevant information from the document and processing for classification
        """
        return True
    
    def analyze_document(self, path:str, doc_type:str, doc_subtype:str, **kwargs):
        """
        Extracting relevant information from the document based on the classification of the document.
        The corresponding analyze function that maps to the document type is retrieved from database
        This method routes control to the appropriate analysis

        :return: JSON representing extracted elements, else False
        """
        if path is None:
            raise ObjectDoesNotExist('File path cannot be empty')

        try:
            t = DocumentType.objects.get(short_code=doc_type)
            analyze_fn = _ANALYZE_METHODS.get(t.short_code)
            if not analyze_fn:
                raise InvalidDocumentType('Document Type %s cannot be analyzed', doc_type)
            return getattr(self, analyze_fn)(path)
        except ObjectDoesNotExist as o:
            logger.error('Document Type is invalid::[doc_type=%s]',doc_type)
            logger.exception(o)
            raise InvalidDocumentType('Document Type %s is invalid or does not exist',doc_type)
        except AttributeError as a:
            logger.error('Unable to process document::[doc_type=%s]::[process_fn=]',doc_type)
            logger.exception(a)
            raise a
        
    def save_document(self, document, doc_type:str, doc_sub_type:int, **kwargs):
        """
        Save an analyzed document in the database. Based on document type classification, save function will differ
        The corresponding save function that maps to the document type is retrieved from database

        :param document The analyzed document JSON / Dict
        :param kwargs
        :return: Document The saved Document model
        """
        if not document or not kwargs.get('user_id'):
            raise Exception('Error saving document::[kwargs=%s]',kwargs)
        
        try:
            t = DocumentType.objects.get(short_code=doc_type)
            s = DocumentSubType.objects.get(pk=doc_sub_type) if doc_sub_type else None
            save_fn = _SAVE_METHODS.get(t.short_code)
            if not save_fn:
                raise InvalidDocumentType('Document Type %s cannot be saved', doc_type)
            return getattr(self, save_fn)(document, t, s, **kwargs)
        except ObjectDoesNotExist as o:
            logger.error('Unable to determine document type / subtype::[doc_type=%s]::[doc_subtype=%s]',doc_type, doc_sub_type)
            logger.exception(o)
            raise o
        except Exception as e:
            logger.error('Unable to save document::[doc_type=%s]::[doc_subtype=%s]',doc_type, doc_sub_type)
            logger.exception(e)
            raise e
    
    def _analyze_expense(self, path:str, **kwargs):
        """
        Extract summary and line item information from expense documents such as receipts or invoices
        
        :param path Path of uploaded file
        :param kwargs 
        :return: JSON representing extracted elements, else False
        """
        _s3_uri = S3Path(path)
        client = boto3.client(
            'textract', 
            region_name=get_app_setting('', 'aws.region')
            )
        
        try:
            response = client.analyze_expense(
                Document={
                    'S3Object': {
                        'Bucket': _s3_uri.bucket,
                        'Name': _s3_uri.key
                    }
                }
            )
            
            return response
        except Exception as e:
            logger.error('Unable to analyze expense::[path=%s]',path)
            logger.exception(e)
            raise e
    
    def _save_expense(self, document, doc_type, doc_subtype=None, **kwargs):
        """
        Parse the analyzed document Dict/JSON and save data into appropriate model instances
        The map of JSON field to model attribute is retrieved from JSON Path map file - aws_expense_doc_map.json

        :param document The JSON/Dict object retrieved from analyze_document function
        :param kwargs
        :return: Integer representing saved Document Id
        """
        parser = ExpenseParser()
        try:
            with transaction.atomic():
                doc = Document.objects.create(
                    user_id=kwargs.get('user_id'),
                    type=doc_type,
                    image_url=kwargs.get('image_url')
                )
                entities = parser.parse(
                    document, 
                    doc.id, 
                    user_id=kwargs.get('user_id')
                )
                for entity_cls, entity in entities.items():
                    entity.save(cascade=True)
                    
            return doc.get_absolute_url()
        except IntegrityError as i:
            logger.error('Error saving expense document')
            logger.exception(i)
            raise i
    
    def _get_s3_bucket_name(self, path):
        """
        Helper method to split S3 URLs and extract bucket name
        """
        _parsed = urlparse(path, allow_fragments=False)
        if _parsed:
            return _parsed.netloc
        else:
            return False

    def _get_s3_file_name(self, path):
        """
        Helper method to split S3 URLs and extract file name
        """
        return os.path.basename(path)
