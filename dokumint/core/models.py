import logging, uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
import mongoengine
from mongoengine import DateField, EmbeddedDocumentField, ObjectIdField
from mongoengine import ReferenceField, StringField

from core import utils
from core.exceptions import InvalidOrMissingDocument
from core.managers import BulkCreateManager
from core.validators import EmailRelayUsernameValidator

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class Creator(models.Model):
    """
    ORM representing document creators e.g. Vendors, Hospitals etc.

    Relationships:
    A creator may have many documents
    A creator belongs to a user
    """

    id = models.AutoField(
        primary_key=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    logo_uri = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    web_url = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    vat_id = models.CharField(
        blank=True,
        db_default='',
        default='',
        max_length=50,
    )
    registration_id = models.CharField(
        blank=True,
        db_default='',
        default='',
        max_length=50,
    )
    other_id = models.CharField(
        blank=True,
        db_default='',
        default='',
        max_length=50,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='creators',
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
    )

    def save(self, document=None, **kwargs):
        # Check if this is an update
        if self.id is not None:
            super().save(**kwargs)
            return
        
        if document is None:
            raise InvalidOrMissingDocument('Missing document association for Creator')
        
        try:
            _creator = Creator.objects.filter(user=self.user).filter(name__iexact=self.name).filter(other_id__iexact=self.other_id)[0]
            if _creator is not None:
                document.creator = _creator
                document.save()
                return
        except IndexError as i:
            pass
        
        super().save(**kwargs)
        document.creator = self
        document.save()

    def __str__(self) -> str:
        return f"{self.name}"
    
    class Meta:
        ordering =  ["created_on"]
        verbose_name = "creator"
        verbose_name_plural = "creators"

class DocumentType(models.Model):
    """
    ORM representing Document Types. Document types are annotated by their short code.
    
    Relationships:
    Document Types have many documents.
    
    Possible values:
    1. Expense - EXP e.g. Receipts & Invoices
    3. Medical Report - MED
    4. Real Estate - RET
    5. Other - OTH
    6. Unidentified - UNI
    """
    short_code = models.CharField(
        max_length=3,
        primary_key=True
    )
    text = models.CharField(
        max_length=100,
        blank=True,
        db_default='',
        default='',
    )
    list_template = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    detail_template = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    analyze_fn = models.CharField(
        max_length=100,
        blank=True,
        db_default='_do_nothing',
        default='_do_nothing',
    )
    save_fn = models.CharField(
        max_length=100,
        blank=True,
        db_default='_do_nothing',
        default='_do_nothing',
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
    )

    def __str__(self) -> str:
        return f"{self.text}"

    class Meta:
        verbose_name = "document type"
        verbose_name_plural = "document types"

class DocumentSubType(models.Model):
    """
    ORM representing Document SubTypes. 
    
    Relationships:
    Document sub-types belong to a document type
    """
    id = models.AutoField(
        primary_key=True,
    )
    type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name='subtypes',
    )
    text = models.CharField(
        blank=True,
        db_default='',
        default='',
        max_length=50,
    )
    list_template = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    detail_template = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    other_field1 = models.CharField(
        max_length=100,
        blank=True,
        db_default='',
        default='',
    )
    other_field2 = models.CharField(
        max_length=100,
        blank=True,
        db_default='',
        default='',
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
    )

    def __str__(self) -> str:
        return f"{self.text} under {self.type.text}"

    class Meta:
        verbose_name = "document subtype"
        verbose_name_plural = "document subtypes"


class Document(models.Model):
    """
    """
    
    type = models.ForeignKey(
        DocumentType,
        on_delete=models.SET_DEFAULT,
        default='UNI',
        related_name='documents',
    ) 
    sub_type = models.ForeignKey(
        DocumentSubType,
        on_delete=models.SET_NULL,
        related_name='documents',
        blank=True,
        null=True,
    )
    review_status = models.BooleanField(
        default=False,
    )
    comments = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    image_url = models.TextField(
        blank=True,
        null=True,
    )
    is_favorite = models.BooleanField(
        default=False,
    )
    is_deleted = models.BooleanField(
        default=False,
    )
    json = models.JSONField(
        null=True
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        null=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents',
    )

    class Meta:
        abstract = True


class ExpenseDocument(Document):
    """
    ORM representing Document object

    Relationships:
    ExpenseDocuments belongs to a type
    ExpenseDocuments may belong to a subtype
    ExpenseDocuments belongs to a creator
    ExpenseDocuments may have one or many addresses
    ExpenseDocuments have one or many dates
    ExpenseDocuments may have one or many line items
    ExpenseDocuments may have one or many tax line items
    ExpenseDocuments may have one or many financial items
    ExpenseDocuments may have one or many tags
    ExpenseDocuments may have one or many identifiers
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    creator = models.ForeignKey(
        Creator,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    line_item_count = models.IntegerField(
        default=0,
        blank=True,
    )
    page_count = models.IntegerField(
        default=1,
        blank=True,
    )

    def __str__(self) -> str:
        return serializers.serialize('json', [self])
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse(
            'core:document_detail', 
            kwargs={ 
                'pk':self.id 
            }
        )
    
    class Meta:
        ordering =  ['created_on']
        verbose_name = 'expense_document'
        verbose_name_plural = 'expense_documents'


class DocumentTag(models.Model):
    """
    ORM representing tags associated with a document
    
    Relationships:
    Document Tags belong to a Document
    """

    id = models.AutoField(
        primary_key=True,
    )
    document = models.UUIDField(
        null=False
    )
    text = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    is_global = models.BooleanField(
        default=False,
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
    )

    def __str__(self) -> str:
        return f"{self.text}"

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"


class EmailRelayLog(models.Model):
    """
    ORM representing email relays received and processed by application

    Relationships:
    EmailRelays belong to a user
    """
    id = models.AutoField(
        primary_key=True,
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="emails",
    )
    from_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    has_attachments = models.BooleanField(
        default=False,
    )
    uri = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    processed = models.BooleanField(
        default=False,
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        null=False,
    )

    def __str__(self) -> str:
        return serializers.serialize('json', [self])

    class Meta:
        verbose_name = "email"
        verbose_name_plural = "emails"


class Profile(models.Model):
    """
    ORM reprenting additional profile information for User. 
    
    Relationships:
    Profile belongs to a User
    """
    email_relay_validator = EmailRelayUsernameValidator()

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
    )
    email_relay = models.CharField(
        max_length=150,
        blank=True,
        unique=True,
        db_default='',
        default='',
        help_text='Required. 150 characters or fewer, comprising of letters, digits, period and underscore only.',
        validators=[email_relay_validator]
    )
    notifications_allowed = models.BooleanField(
        default=False
    )
    analytics_allowed = models.BooleanField(
        default=False
    )
    storage_bucket = models.TextField(
        blank=True,
        null=True,
    )
    postal_code = models.CharField(
        max_length=11,
        blank=True,
        db_default='',
        default='00000',
        verbose_name='Zipcode',
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        null=False,
    )

    def __str__(self) -> str:
        return f"{self.user}"

    class Meta:
        verbose_name = "profile"
        verbose_name_plural = "profiles"


class TransactionLog(models.Model):
    """
    ORM representing user transactions related to 
    - document processing
    - credit purchase
    """

    id = models.AutoField(
        primary_key=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    tx_type = models.CharField(
        max_length=10,
        blank=True,
        null=True,
    )
    tx_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    document = models.UUIDField(       
        null=True,
    )
    tx_amt = models.DecimalField(
        decimal_places=2,
        max_digits=8,
        default=0.0,
        blank=True,
    )
    auth_code = models.CharField(
        max_length=255,
        blank=True,
        db_default='',
        default='',
    )
    created_on = models.DateField(
        auto_now_add=True,
        null=False,
    )

    def __str__(self) -> str:
        return f"{self.tx_type}"

    class Meta:
        verbose_name = "transaction"
        verbose_name_plural = "transactions"


class UserStat(models.Model):
    """
    Profile Statistics about user. Also includes summary statistics such as 
    1. Total receipts processed
    2. Total line items processed
    3. Number of credits available as of date
    4. Number of credits used till date

    Relationships:
    User statistics belong to a User
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name="stats",
    )
    credits_balance = models.IntegerField(
        default=100
    )
    credits_used = models.IntegerField(
        default=0
    )
    pro_document_count = models.IntegerField(
        default=0
    )
    pro_line_item_count = models.IntegerField(
        default=0
    )
    created_on = models.DateTimeField(
        auto_now=True,
        null=False,
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        null=False,
    )

    def __str__(self) -> str:
        return f"{self.user}"

    class Meta:
        verbose_name = "user statistic"
        verbose_name_plural = "user statistics"