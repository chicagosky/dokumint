import logging, re
from dateutil.parser import parse as ParseDate
from dateutil.parser import ParserError
from django.conf import settings
from django.utils.module_loading import import_string
from jsonpath_ng.ext import parser
from jsonpath_ng.exceptions import JsonPathLexerError
from mongoengine import StringField

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

# Regular expression to find floating values in strings
REG_EXP_FIND_DECIMAL_VALUE = "[-+]?(\\d+(\\.\\d*)?|\\.\\d+)([eE][-+]?\\d+)?"

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


def get_field_type_class(field_type, **kwargs):
    """
    """
    try:
        return import_string(field_type)
    except LookupError:
        logger.debug('Error retrieving field type class::[field_type=%s]', field_type)
        if not kwargs.get('fail_silently'):
            raise
        else:
            return None
            

def get_field_path(field_json_obj, **kwargs):
    """
    """
    json_path = field_json_obj.get('path')
    if json_path is not None:
        if 'key' in kwargs and 'value' in kwargs:
            json_path = json_path.replace(kwargs.get('key'), kwargs.get('value'))
    return json_path


def get_field_converter_fn(field_json_obj, **kwargs):
    """
    """
    try:
        _converter_fn_name = field_json_obj.get('converter')
        if _converter_fn_name is not None:
            return import_string(_converter_fn_name)
    except AttributeError as a:
        logger.error('Error getting converter function::[field_json_obj=%s]',field_json_obj)
        logger.error(a)
    
    return None


def get_field_extractor_fn_name(field_json_obj, **kwargs):
        """
        """
        try:
            extractor_fn_name = field_json_obj.get('extractor')
            return extractor_fn_name
        except AttributeError as a:
            logger.error('Error getting converter function::[field_json_obj=%s]',field_json_obj)
            logger.error(a)
        
        return None


def extract_value_from_document(document, path, converter_fn, **kwargs):
    """
    """
    try:
        expr = parser.parse(path)
        values = [match.value for match in expr.find(document)]
        if values is None or not values:
            return None
        #logger.debug('Pre-conversion::[values=%s]::[converter_fn=%s]',values,converter_fn)
        if type(values) == list :
            if kwargs.get('with_max_confidence'):
                #logger.debug('Converted Value::[value=%s]',converter_fn(values[0]))
                return converter_fn(values[0]) if converter_fn else values[0]
            else:
                #logger.debug('Converted Value::[value=%s]',map(converter_fn, values))
                return map(converter_fn, values) if converter_fn else values
        else:
            #logger.debug('Converted Value::[value=%s]',converter_fn(values))
            return converter_fn(values) if converter_fn else values
    except JsonPathLexerError as j:
        logger.error('Error parsing JSON path::[path=%s]',path)
        logger.exception(j)
        raise j
    except Exception as e:
        logger.error('Error converting value::[values=%s]::[converter_fn=%s]',values,converter_fn)
        raise e
        
        
def clean_value(entity, field, value, **kwargs):
    """
    """
    try:
        if hasattr(entity, field):
            if isinstance(entity._fields.get(field), StringField):
                max_length = entity._fields.get(field).max_length
                value = value[:max_length]
    except Exception as e:
        logger.error('Error cleaning value::[entity=%s]::[field=%s]::[value=%s]',entity,field,value)
        logger.error(e)
    
    return value


def extract_simple_field(field_json_obj, document, **kwargs):
    """
    """
    json_path = get_field_path(field_json_obj, **kwargs)
    if not json_path:
        return
    converter_fn = get_field_converter_fn(field_json_obj, **kwargs)
    value = extract_value_from_document(document, json_path, converter_fn, with_max_confidence=True)
    return value


def extract_nested_field(field_json_obj, document, **kwargs):
    """
    """
    field_cls = get_field_type_class(field_json_obj.get('type'))
    field = field_cls()