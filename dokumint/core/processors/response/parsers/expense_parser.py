import jsonpickle, logging
from django.conf import settings
from django.utils.module_loading import import_string
from jsonpath_ng.ext import parser

from core.mongo import ExpenseDocument
from core.processors.response.parsers.aws_maps import AWSMaps
from core.processors.response.parsers.utils import clean_value, extract_value_from_document
from core.processors.response.parsers.utils import get_field_converter_fn, get_field_extractor_fn_name, get_field_path
from core.processors.response.parsers.utils import get_field_type_class

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class ExpenseParser():
    """
    """

    def parse(self, document, document_id, **kwargs):
        """
        Parses an analyze_expense response and returns a dictionary of populated MongoEngine Document objects.
        The parsing is done with the aid of a map that provides JSON paths for corresponding Model fields.
        """
        if not self._is_valid_document(document) or not document_id:
            raise Exception('Invalid expense analysis document::[document_id=%s]',document_id)

        _entity_maps = self.get_json_map()['entities']
        self.entities = {}
        self._populate_entities(_entity_maps, document)
        expense = self.entities.get(ExpenseDocument)
        if expense is not None and kwargs.get('user_id') is not None:
            expense.user_id = int(kwargs['user_id'])
        return self.entities
    
    def _populate_entities(self, entity_maps, document, **kwargs):
        """
        Populates MongoEngine Document objects (called entities to avoid confusion with expense documents)
        Returns a dictionary of Document objects
        """
        for entity_map in entity_maps:
            entity_class = self._get_entity_class(entity_map,  fail_silently=True)
            if entity_class is None:
                continue
            entity = self._populate_fields(entity_class(), entity_map.get('field_paths'), document)
            self.entities[entity_class] = entity

    def _populate_fields(self, entity, field_paths, document, **kwargs):
        """
        Extracts field values from analyze_expense response using JSON field paths associated with entity fields 
        Returns the populated entity object 
        """
        for entity_field, field_json_obj in field_paths.items():
            _extractor_fn_name = get_field_extractor_fn_name(field_json_obj, **kwargs)
            if not _extractor_fn_name:
                continue
            _extractor_fn = getattr(self, _extractor_fn_name)
            value = _extractor_fn(field_json_obj, document, **kwargs)
            if value is not None:
                value = clean_value(entity, entity_field, value)
                setattr(entity, entity_field, value)
        return entity
    
    def extract_simple_field(self, field_json_obj, document, **kwargs):
        """
        Extracts the value of a simple data type (String, Integer, Decimal, Date etc.) from analyze_expense response
        using JSON paths
        """
        json_path = get_field_path(field_json_obj, **kwargs)
        if not json_path:
            return
        converter_fn = get_field_converter_fn(field_json_obj, **kwargs)
        value = extract_value_from_document(document, json_path, converter_fn, with_max_confidence=True)
        return value
    

    def extract_nested_field(self, field_json_obj, document, **kwargs):
        """
        Extracts a nested field with additional nest fields or simple fields underneath
        """
        field_cls = get_field_type_class(field_json_obj.get('type'))
        field = self._populate_fields(field_cls(), field_json_obj.get('field_paths'), document, **kwargs)
        return field
    

    def extract_list_of_nested_field(self, field_json_obj, document, **kwargs):
        """
        Extracts a list of nested fields with additional nested fields or simple fields underneath
        """
        size = parser.parse(field_json_obj.get('count')).find(document)[0].value
        
        nested_fields = []
        for x in range(size):
            _field = self.extract_nested_field(
                field_json_obj,
                document,
                key='{#}',
                value=str(x),
                with_max_confidence=True
            )
            nested_fields.append(_field)
        return nested_fields
    

    def extract_grouped_nested_field(self, field_json_obj, document, **kwargs):
        """
        Extracts nested fields that are grouped by a common value or attribute
        """
        nested_fields = []
        group_key = field_json_obj.get('group_by').get('key')
        groups = extract_value_from_document(
            document, 
            field_json_obj.get('group_by').get('groups_path'), 
            False
        )
        if groups:
            for group in groups:
                grouped_extract = extract_value_from_document(
                    document, 
                    field_json_obj.get('group_by').get('grouped_value_path').replace(group_key, group), 
                    False
                )
                _field_cls = get_field_type_class(field_json_obj.get('type'))
                _field = self._populate_fields(
                    _field_cls(),
                    field_json_obj.get('field_paths'), 
                    grouped_extract, 
                    with_max_confidence=True
                )
                nested_fields.append(_field)
        return nested_fields
    

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
        Retrieves corresponding map that translates response from analyze_expense
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