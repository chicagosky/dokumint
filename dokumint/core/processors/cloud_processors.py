import abc, importlib, logging
from io import BytesIO 

from django.conf import settings
from django.core.files.base import File

from core.models import Document
from core.utils import get_app_setting

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class DocumentProcessorAbstractClass(metaclass=abc.ABCMeta):
    
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'create_storage') and 
                callable(subclass.create_storage) and 
                hasattr(subclass, 'create_folder') and 
                callable(subclass.create_folder) and 
                hasattr(subclass, 'download_document_to_stream') and 
                callable(subclass.download_document_to_stream) and 
                hasattr(subclass, 'classify_document') and 
                callable(subclass.classify_document) and 
                hasattr(subclass, 'analyze_document') and 
                callable(subclass.analyze_document) and 
                hasattr(subclass, 'save_document') and 
                callable(subclass.save_document) and 
                hasattr(subclass, 'upload_document') and 
                callable(subclass.upload_document) or 
                NotImplemented)

    def get_cloud_processor():
        """
        Dynamically instantiate and return configured cloud processor that is a child of ReceiptProcessorAbstractClass

        :return: Cloud processor instance 
        """
     
        try:
            # Instantiate configured processor
            module = importlib.import_module(get_app_setting('', 'cloud_processor.module'))
            processor_class = getattr(module, get_app_setting('', 'cloud_processor.class'))
            return processor_class()
        except Exception as e:
            logger.exception(e)
            raise e
    
    @abc.abstractmethod
    def create_storage(self, bucket_name: str, **kwargs) -> str:
        """
        Create a Cloud Storage bucket in a specified region

        :param folder_name: Bucket to create
        :return: Bucket name if created False if bucket not created
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    def create_folder(self, bucket_name: str, folder_name: str, **kwargs) -> str:
        """
        Create a Cloud Storage folder in a specified bucket

        :param bucket_name: Bucket where the folder will be created
        :param folder_name: Folder name to create
        :return: Folder name if created False if bucket not created
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    def upload_document(self, file: File, file_ext: str, bucket_name: str, **kwargs):
        """
        Upload a document to a cloud storage bucket

        :param file: File to upload
        :param file_ext: Extension of file being uploaded
        :param bucket_name: Bucket to upload to
        :return: Uploaded file path if file was uploaded, else False
        """
        raise NotImplementedError

    @abc.abstractmethod
    def download_document_to_stream(self, file_name: str, bucket: str, stream_obj: BytesIO, **kwargs):
        """
        Download file from Cloud Storage bucket to byte stream

        :param file_name: File to download
        :param bucket: Bucket hosting the file
        :param stream_obj: BytesIO stream representing the downloaded file
        :return: Byte stream representing file if successful, False if not successful
        """
        raise NotImplementedError

    @abc.abstractmethod
    def classify_document(self, path: str, **kwargs):
        """
        Process user uploaded document and classify
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    def analyze_document(self, path: str, doc_type:None, doc_subtype:None, **kwargs):
        """
        Process user uploaded document and convert to an Iterable [Array]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_document(self, document, doc_type:str, doc_subtype:str, **kwargs):
        """
        Save parsed document in SQL tables
        """
        raise NotImplementedError

    