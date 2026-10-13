import logging
from pydoc import doc
from re import T

from django.conf import settings
from django.utils.module_loading import import_string
from jsonpath_ng.ext import parser
from jsonpath_ng.exceptions import JsonPathLexerError
from mongoengine import StringField

from core.processors.response.parsers.utils import get_field_extractor_fn, clean_value
from core.processors.response.parsers.aws_maps import AWSMaps

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class AWSAnalyzeExpenseParser():

    def parse(self, document, document_id, **kwargs):
        """
        Parses an AWS Textract analyze_expense response and returns a dictionary of populated Model objects.
        The parsing is done with the aid of a map that provides JSON paths for corresponding Model fields.
        """
        if not self._is_valid_document(document) or not document_id:
            raise Exception('Invalid Textract response document::[document_id=%s]',document_id)

        _entity_maps = self.get_json_map()['entities']
        self.entities = {}
        self._populate_entities(_entity_maps, document)           
        return self.entities
    
    def _populate_entities(self, entity_maps, document, **kwargs):
        """
        """
        for entity_map in entity_maps:
            entity_class = self._get_entity_class(entity_map,  fail_silently=True)
            if entity_class is None:
                continue
            entity = self._populate_entity_fields(entity_class(), entity_map.get('field_paths'), document)
            self.entities[entity_class] = entity
        
        
    def _populate_entity_fields(self, entity, field_paths, document, **kwargs):
        """
        """
        for entity_field, field_json_obj in field_paths.items():
            _extractor_fn = get_field_extractor_fn(field_json_obj, **kwargs)
            if not _extractor_fn:
                continue
            value = _extractor_fn(field_json_obj, document, **kwargs)
            if value is not None:
                value = clean_value(entity, entity_field, value)
                setattr(entity, entity_field, value)
        return entity
    
    def get_field_type_class(self, field_type, **kwargs):
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
                

    def get_field_path(self, field_json_obj, **kwargs):
        """
        """
        json_path = field_json_obj.get('path')
        if json_path is not None:
            if 'key' in kwargs and 'value' in kwargs:
                json_path = json_path.replace(kwargs.get('key'), kwargs.get('value'))
        return json_path


    def get_field_converter_fn(self, field_json_obj, **kwargs):
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


    def get_field_extractor_fn(self, field_json_obj, **kwargs):
        """
        """
        try:
            _extractor_fn_name = field_json_obj.get('extractor')
            if _extractor_fn_name is not None:
                return import_string(_extractor_fn_name)
        except AttributeError as a:
            logger.error('Error getting converter function::[field_json_obj=%s]',field_json_obj)
            logger.error(a)
        
        return None


    def extract_value_from_document(self, document, path, converter_fn, **kwargs):
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
            
            
    def clean_value(self, entity, field, value, **kwargs):
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


    def extract_simple_field(self, field_json_obj, document, **kwargs):
        """
        """
        json_path = self.get_field_path(field_json_obj, **kwargs)
        if not json_path:
            return
        converter_fn = self.get_field_converter_fn(field_json_obj, **kwargs)
        value = self.extract_value_from_document(document, json_path, converter_fn, with_max_confidence=True)
        return value


    def extract_nested_field(self, field_json_obj, document, **kwargs):
        """
        """
        field_cls = self.get_field_type_class(field_json_obj.get('type'))
        field = field_cls()
    


    
    def convert_map_to_mongo_document(self, entity_map, document, **kwargs):
        """
        Converts portion of an AWS Textract analyze_expense response into a JSON object using JSON paths to
        translate to pre-defined JSON structure
        """
        _entity_class = self._get_entity_class(entity_map,  fail_silently=kwargs.get('fail_silently'))
        if _entity_class is None:
            return None
        
        try:
            if entity_map.get('group_by'):
                _entities = self._populate_entity_by_group(
                    _entity_class, 
                    entity_map, 
                    document,
                    document_id=kwargs.get('document_id'), 
                    user_id=kwargs.get('user_id'),
                )
                self.entities[_entity_class] = _entities
            elif entity_map.get('is_bulk_load'):
                _entities = self._populate_entity_for_bulk_load(
                    _entity_class, 
                    entity_map, 
                    document,
                    document_id=kwargs.get('document_id'), 
                    user_id=kwargs.get('user_id')
                )
                self.entities[_entity_class] = _entities
            else:
                _entity = self._populate_entity(
                    _entity_class, 
                    entity_map, 
                    document, 
                    document_id=kwargs.get('document_id'), 
                    user_id=kwargs.get('user_id'),
                    with_max_confidence=True
                )
                self.entities[_entity_class] = _entity
        except Exception as e:
            logger.error('Error parsing Textract response::[_model_class=%s]',_entity_class)
            logger.exception(e)
            raise e


    def _populate_entity_for_bulk_load(self, entity_class, map, document, **kwargs):
        """
        Populate Model instances for bulk load with data from AWS Textract analyze_expense response
        """
        from jsonpath_ng import parser
        size = parser.parse(map.get('bulk_size')).find(document)[0].value
        
        entities = []
        for x in range(size):
            _model = self._populate_entity(
                entity_class, 
                map, 
                document, 
                document_id=kwargs.get('document_id'), 
                user_id=kwargs.get('user_id'),
                key='{#}', 
                value=str(x), 
                with_max_confidence=True
            )
            entities.append(_model)
        return entities


    def _populate_entity_by_group(self, entity_class, map, document, **kwargs):
        """
        """
        group_key = map.get('group_by').get('key')
        entities = []
        groups = self._extract_value_from_document(document, map.get('group_by').get('groups_path'), False)
        if groups:
            for group in groups:
                grouped_extract = self._extract_value_from_document(
                    document, 
                    map.get('group_by').get('grouped_value_path').replace(group_key, group),
                    False
                )
                _entity = self._populate_entity(
                    entity_class, 
                    map, 
                    grouped_extract, 
                    document_id=kwargs.get('document_id'), 
                    user_id=kwargs.get('user_id'),
                    with_max_confidence=True
                )
                entities.append(_entity)
        return entities

    
    

    def _is_valid_document(self, document):
        """
        Checks if response document from AWS Textract analyze_expense is valid

        :returns: True if valid, False otherwise
        """
        if document is not None or not document:
            if type(document) == dict:
                return True
            
        return False

    def get_json_map(self):
        """
        Retrieves corresponding map that translates response from AWS Textract analyze_expense
        to corresponding Dokumint models and attributes. The retrieved map is also a JSON dictionary
        with various model names as keys
        {   
            models : [
                {
                    model : <model_name>,
                    map : {
                        <field_name> : {
                            path : <json_path>
                        },
                        ...
                    }
                },
                ...
            ]
        }
        """
        return AWSMaps.ANALYZE_EXPENSE_MAP

    def _get_entity_class(self, map, **kwargs):
        """
        Return the MongoEngine document matching the given app_label and document_name.

        As a shortcut, app_label may be in the form <app_label>.<document_name>.

        document_name is case-insensitive.

        Raise LookupError if no application exists with this label, or no
        model exists with this name in the application. Raise ValueError if
        called with a single argument that doesn't contain exactly one dot.
        """
        try:
            _entity_name = map.get('entity')
            if _entity_name is None:
                return None
            return import_string(_entity_name)
        except LookupError:
            logger.debug('Error retrieving entity class::[_entity_name=%s]::[map=%s]', _entity_name, map)
            if not kwargs.get('fail_silently'):
                raise
            else:
                return None
 