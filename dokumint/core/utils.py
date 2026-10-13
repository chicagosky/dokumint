import base64, importlib, logging, magic, os, re, sys, uuid
from dateutil.parser import parse as ParseDate
from dateutil.parser import ParserError
from functools import reduce

from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ObjectDoesNotExist
from django.forms.utils import ErrorDict
from django.utils.crypto import get_random_string

from core.messages import ErrorMessages

# max bytes to read for file type detection
FILE_DETECT_READ_SIZE = 2048

# Regular expression to find floating values in strings
REG_EXP_FIND_DECIMAL_VALUE = "[-+]?(\\d+(\\.\\d*)?|\\.\\d+)([eE][-+]?\\d+)?"

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

def get_app_setting(app:str, label:str):
    """
    Retrieves setting for corresponding label (dot notation)
    """
    app = 'DOKUMINT_SETTINGS' if not app else app
    _keys = label.split('.')
    value = getattr(settings, app)
    for _key in _keys:
        value = value[_key]

    return value


def convert_to_nice_form_errors(form):
    """
    Converts form errors to use field labels instead of database field names
    """
    nice_errors = ErrorDict()
    try:
        for field, errors in form.errors.items():
            if field == NON_FIELD_ERRORS:
                key = ErrorMessages.NON_FIELD_ERROR_MSG_LABEL
            else:
                key = form.fields[field].label
            nice_errors[key] = errors
    except Exception as e:
        logger.error(e)

    return nice_errors


def deep_get(dictionary, keys, default=None):
    """
    Get elements from a nested dictionary with a single statement
    https://stackoverflow.com/a/36131992/776543
    """
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


def encode_image(image):
    """
    Encode an image into a Base64 string
    
    :param image Image file to be encoded
    :return: String Base64 encoded image string
    """
    try:
        return base64.b64encode(image.read())
    except Exception as e:
        logger.error(e)
        raise e
    

def get_class(module_name, class_name):
    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def get_file_type(fileobj):
    """
    Detects MIME type of provided file
    This is done using the Python Magic library
    """
    if fileobj is None or not fileobj:
        raise ObjectDoesNotExist('Invalid File::[fileobj=%s]',fileobj)

    detected_type = magic.from_buffer(fileobj.read(FILE_DETECT_READ_SIZE), mime=True)
    return detected_type


def get_file_extension(filename):
    """
    Get extension of provided file object
    """
    file_extension = os.path.splitext(filename)[1]
    if file_extension is None or not file_extension:
        # raise error
        pass

    return file_extension


def get_randomized_username(username:str, max_length:int, with_random:bool, random_seperator:str = '-'):
        """
        Helper function to generate username + random string. Used for creating S3 buckets and email relays
        """
        username.replace('.', '_')
        result = username[:6] if len(username) > 6 else username
        _random_length = max_length - len(result)
        if with_random and _random_length>0:
            result = result + random_seperator \
                        + get_random_string(length=_random_length).lower()
        return result


def generate_slug(length=22, strings=None):
    """
    Generate a random slug of specified length. If length is specified then the slug is truncated accordingly
    If an iterable of strings is provided, then the initial slug generated is comprised of the provided strings
    with random strings completing the desired length
    """
    return str(uuid.uuid1()).lower()


def is_repetitive_number(s:str) -> bool:
    """
    Verifies if string is a repetitive number 
    e.g. 1111 or 0000
    
    :param s String to be verified
    :return: bool True if it is a repetitive number otherwise False
    """
    if set(s) == 1:
        return True

    return False


def is_sequential_number(s:str) -> bool:
    """
    Verifies if string is a sequential numbers
    e.g. 1234 or 6789
    
    :param s String to be verified
    :return: bool True if it is a sequential number otherwise False
    """

    # To be implemented
    return False

def parse_str(s:str):
    """
    Parses a given string and strips leading, middle and trailing spaces
    """
    try:
        value = re.sub('\\s+', ' ', str(s))
        return value
    except Exception as e:
        logger.error('Error parsing string::[s=%s]',s)
        logger.error(e)
    return ''


def parse_str_to_date(s:str):
    """
    Parse a string to date. 

    :param str String to be parsed
    :returns: Date parsed or False if an error occurs
    """
    try:
        return ParseDate(s)
    except ParserError as e:
        logger.error(f'Parse to date error: {s}', e)
        return False


def parse_str_to_float(s:str) -> float:
    """
    Parse a string to float
    
    :param str String to be parsed
    :return: float Parsed float value or 0.0
    """
    try:
        match = re.search(REG_EXP_FIND_DECIMAL_VALUE, s)
        if match:
            return float(match[0])
        else:
            return 0.0
    except ValueError as e:
        logger.error(f'Parse to float error: {s}', e)
        return 0.0


def safeget(dct, *keys):
    """
    Safely retrieve nested values from a dictionary
    https://stackoverflow.com/a/25833661/776543
    """
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct


def validate_bank_card_digits(s:str):
    """
    Validates if the provided string is a credit or debit card number
    
    :param s String of digits that needs to be validated
    :return: str Last 4 digits of card number if valid or False if invalid
    """
    # Length check, credit card strings are usually 4 digits (last 4) or 16 digits
    s = s.strip()
    l = len(s)
    if l<4 or l>16:
        return False
    
    # If length is greater than 4, extract last 4 digits for check
    if l>4:
        s = s[-4:]

    # Check if string is numeric, non-repetitive and not sequential numbers
    if s.isnumeric():
        if is_repetitive_number(s) == False and is_sequential_number(s) == False:
            return s
                
    return False
