from django import template
from django.db import models
from django.template.loader import get_template
from rest_framework.utils.serializer_helpers import ReturnDict

register = template.Library()

@register.inclusion_tag('tags/document_list.html')
def render_document_list_item(document, template='tags/expense_document_list.html'):
    return {
        'document': document,
        'template': template,
        'id': document.id,
        'transaction_date': document.dates.transaction_date,
        'creator_name': document.creator.name,
        'type': document.type.short_code,
        'item_count': document.expense_line_items.count,
        'total': document.financials.total,
        'favorited': document.is_favorite
    }

@register.inclusion_tag('tags/document_address.html')
def document_address(address):
    return {
        'address_type': address.address_type,
        'line_1': address.line_1,
        'city': address.city,
        'state': address.state,
        'postal_code': address.postal_code,
        'country': address.country
        }

@register.inclusion_tag('tags/document_dates.html')
def document_dates(dates):
    _dates = {}
    _fields = dates._meta.get_fields()
    for _field in _fields:
        if type(_field)==models.DateField:
            _dates[_field.verbose_name] = _field.value_from_object(dates)
    return {
        'dates': _dates
        }

@register.inclusion_tag('tags/document_favorite.html')
def document_favorite(document):
    return {
            'favorited': document.is_favorite,
            'id': document.id
        }

@register.inclusion_tag('tags/document_expense_line_item.html')
def expense_line_items(line_item):
    return {
        'line_item': line_item,
        'document_id': line_item.document_id
        }