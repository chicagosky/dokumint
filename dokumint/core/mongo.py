import jsonpickle, logging

from django.conf import settings
from mongoengine import Document, EmbeddedDocument, DO_NOTHING
from mongoengine import DateField, DecimalField, EmbeddedDocumentField, EmbeddedDocumentListField
from mongoengine import IntField, ReferenceField, StringField

from core import utils

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class Creator(Document):
    """
    """
    
    name = StringField(
        max_length=255,
        default='',
    )
    logo_uri = StringField(
        max_length=255,
        default='',
    )
    web_url = StringField(
        max_length=255,
        default='',
    )
    vat_id = StringField(
        default='',
        max_length=50,
    )
    registration_id = StringField(
        default='',
        max_length=50,
    )
    other_id = StringField(
        default='',
        max_length=50,
    )

    def __str__(self):
        return jsonpickle.encode(self)


class DocumentAddress(EmbeddedDocument):
    """
    ORM representing addresses found in a document
    
    Relationships:
    Addresses belong to a document
    """

    address_type = StringField(
        max_length=50,
        null=True,
    )
    addressee = StringField(
        max_length=50,
        null=True,
    )
    line_1 = StringField(
        max_length=100,
        null=True,
    )
    line_2 = StringField(
        max_length=100,
        null=True,
    )
    city = StringField(
        max_length=50,
        null=True,
    )
    state = StringField(
        max_length=50,
        null=True,
    )
    postal_code = StringField(
        default='00000',
        max_length=11,
        verbose_name='Zipcode',
    )
    country = StringField(
        max_length=100,
        null=True,
    )

    def __str__(self):
        return jsonpickle.encode(self)
 

class ExpenseDates(EmbeddedDocument):
    """
    ORM representing various date types and values found on an Expense Document

    Relationships:
    Expense Dates belongs to an Expense Document
    """
    
    transaction_date = DateField(
        null=True,
        verbose_name='Transaction Date'
    )
    due_date = DateField(
        null=True,
        verbose_name='Due Date'
    )
    ship_date = DateField(
        null=True,
        verbose_name='Ship Date'
    )
    delivery_date = DateField(
        null=True,
        verbose_name='Delivery Date'
    )
    start_date = DateField(
        null=True,
        verbose_name='Start Date'
    )
    end_date = DateField(
        null=True,
        verbose_name='End Date'
    )
    other_date = DateField(
        null=True,
    )

    def __str__(self):
        return jsonpickle.encode(self)


class ExpenseFinancials(EmbeddedDocument):
    """
    ORM representing various financials associated with an expense document
    
    Relationships:
    Expense Financials belong to an Expense Document
    """
    
    subtotal = DecimalField(
        precision=2,
        default=0.0,
    ) 
    discount = DecimalField(
        precision=2,
        default=0.0,
    ) 
    cashback = DecimalField(
        precision=2,
        default=0.0,
    ) 
    tip = DecimalField(
        precision=2,
        default=0.0,
    ) 
    total = DecimalField(
        precision=2,
        default=0.0,
    ) 
    balance_due = DecimalField(
        precision=2,
        default=0.0
    ) 
    currency_code = StringField(
        max_length=4,
        null=True,
    )

    def __str__(self):
        return jsonpickle.encode(self)


class ExpenseIdentifiers(EmbeddedDocument):
    """
    ORM representing various identifiers in an expense document
    
    Relationships:
    Document Identifiers belongs to an Expense Document
    """
    
    account_id = StringField(
        max_length=100,
        null=True,
    )
    invoice_id = StringField(
        max_length=100,
        null=True,
    )
    po_id = StringField(
        max_length=100,
        null=True,
    )
    reference_id = StringField(
        max_length=100,
        null=True,
    )
    other_id = StringField(
        max_length=100,
        null=True,
    )

    def __str__(self):
        return jsonpickle.encode(self)


class ExpenseLineItem(EmbeddedDocument):
    """
    ORM representing line items in an expense document.
    
    Relationships:
    Expense Line Items belongs to an Expense Document
    """
    
    date = DateField(
        null=True,
    )
    sku = StringField(
        max_length=50,
        default='',
    )
    upc = StringField(
        max_length=50,
        null=True,
    )
    description = StringField(
        max_length=255,
        null=True,
    )
    quantity = DecimalField(
        precision=2,
        default=1.0,
    )
    discount_amt = DecimalField(
        precision=2,
        default=0.0,
    )
    discount_rate = DecimalField(
        precision=2,
        default=0.0, 
    )
    unit_measure = StringField(
        max_length=50,
        null=True,
    )
    unit_price = DecimalField(
        precision=2,
        default=0.0, 
    )
    total = DecimalField(
        precision=2,
        default=0.0, 
    )

    def __str__(self):
        return jsonpickle.encode(self)
        

class ExpenseTax(EmbeddedDocument):
    """
    ORM representing identified tax items in an expense document
    
    Relationships:
    Document Tax Line Items belongs to an Expense Document
    """

    tax_name = StringField(
        max_length=100,
        null=True,
    )
    tax_rate = DecimalField(
        precision=2,
        default=0.0,
    ) 
    tax_total = DecimalField(
        precision=2,
        default=0.0,
    ) 
    tax_base = DecimalField(
        precision=2,
        default=0.0,
    ) 

    def __str__(self):
        return jsonpickle.encode(self)
        

class ExpenseDocument(Document):
    """
    """
    creator = ReferenceField(Creator, reverse_delete_rule=DO_NOTHING)
    addresses = EmbeddedDocumentListField(DocumentAddress)
    dates = EmbeddedDocumentField(ExpenseDates)
    financials = EmbeddedDocumentField(ExpenseFinancials)
    identifiers = EmbeddedDocumentField(ExpenseIdentifiers)
    line_items = EmbeddedDocumentListField(ExpenseLineItem)
    taxes = EmbeddedDocumentListField(ExpenseTax)

    type = StringField(
        max_length=3,
        default='EXP'
    )
    sub_type = StringField(
        max_length=3,
    )
    user_id = IntField()

    def __str__(self):
        return jsonpickle.encode(self)

