import base64, json, os, requests
import boto3
import mailparser

def lambda_handler(event, context):
    """
    """
    s3 = boto3.client('s3')

    def get_email_relay_username(addresses):
        """
        Extracts the relevant username to use for profile lookup from array of 'to' email addresses
        """
        if not addresses:
            return False
        
        for address in addresses:
            # Each address is a tuple of two elements, index 0 is Name, index 1 is email address
            _email_parts = address[1].split('@')
            if _email_parts[1] == 'dokumint.ai':
                return _email_parts[0]
            
        return False
    
    def move_email(source_bucket: str, dest_bucket:str, filename: str):
        """
        Copies email file object from email relay S3 bucket to user specific S3 bucket
        Deletes file from email relay S3 bucket after successful copy
        """
        _dest_key = 'email-relay/' + filename
        try:
            s3.copy(
                {'Bucket': source_bucket,
                'Key': filename}, 
                dest_bucket, 
                _dest_key
            )
            s3.delete_object(
                Bucket=source_bucket,
                Key=filename
            )
        except Exception as e:
            return False
        return _dest_key
    
    def get_file_extension(filename):
        """
        Get extension of provided file object
        """
        file_extension = os.path.splitext(filename)[1]
        if file_extension is None or not file_extension:
            return False

        return file_extension

    # Retrieve triggering email details from SNS message
    message = json.loads(event['Records'][0]['Sns']['Message'])
    _source_bucket = message["receipt"]["action"]["bucketName"]
    _filename = message["receipt"]["action"]["objectKey"]

    # Retrieve and parse email stored as file in S3
    
    response = s3.get_object(Bucket=_source_bucket, Key=_filename)
    emailcontent = response['Body'].read() # Byte stream
    mail = mailparser.parse_from_bytes(emailcontent)

    # Identify email relay user details
    addresses = (mail.to or []) + (mail.cc or []) + (mail.bcc or [])
    _lookup_username = get_email_relay_username(addresses)
    if not _lookup_username:
        return False #TODO: Log invalid email relay
    _lookup_url = os.environ['PROFILE_LOOKUP_URL'] + '?search=' + _lookup_username
    headers = {
        'Authorization': 'Api-Key ' + os.environ['DOKUMINT_API_KEY'],
        'content-type': 'application/x-www-form-urlencoded'
    }
    response = requests.get(_lookup_url, headers=headers)
    if not response.status_code == 200:
        return False
    response = response.json()
    
    _user_id = response[0]['user']
    _user_bucket = response[0]['storage_bucket']

    # Move email object to user's storage bucket
    email_uri = move_email(_source_bucket, _user_bucket, _filename)

    # Log email relay
    requests.post(os.environ['LOG_EMAIL_RELAY_URL'],
                  headers=headers,
                  data={
                      'user': _user_id,
                      'from_id': mail.from_,
                      'subject': mail.subject,
                      'has_attachments': True if mail.attachments else False,
                      'uri': email_uri,
                      'processed': False
                  }
                )
    
    # Process each attached document
    for attachment in mail.attachments:
        _attach_name = attachment['filename']
        _extension = get_file_extension(_attach_name)
        _attach_con_type = attachment['mail_content_type']
        _payload = attachment['payload']
        _type = 'EXP'
        
        upload_response = requests.post(os.environ['UPLOAD_DOCUMENT_URL'], 
                                 headers=headers, 
                                 data={
                                     'file':_payload,
                                     'file_ext':_extension,
                                     'user_id': _user_id,
                                     'base64encoded': True
                                     }
                                )
        upload_response = upload_response.json()
        analysis_response = requests.post(os.environ['ANALYZE_DOCUMENT_URL'], 
                                 headers=headers, 
                                 data={
                                     's3_uri':upload_response['s3_uri'],
                                     'type': 'EXP',
                                     'user_id': _user_id
                                     }
                                )
        if analysis_response.status_code != 200:
            print('Document analysis failed', analysis_response.status_code)
    return message

