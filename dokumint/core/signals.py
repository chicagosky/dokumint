import logging

from allauth.socialaccount.models import SocialAccount
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string

from core.exceptions import InvalidCloudStorage
from core.models import Document
from core.models import Profile, TransactionLog, UserStat
from core.models import TransactionLog
from core.models import UserStat
from core.managers import bulk_created
from core.processors.cloud_processors import DocumentProcessorAbstractClass
from core.utils import get_app_setting, get_randomized_username

logger = logging.getLogger(settings.DOKUMINT_SETTINGS['default']['logger'])

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Executed when a new user account is created and saved. The following steps are executed in order
    1. A user Profile model object is created
    2. A Cloud storage bucket is created and linked to the Profile
    3. An entry is created in the user statistics table with default credit balance
    4. An entry is logged in the transaction log table for credit amount
    """
    if not created:
        return

    try:
        # Create User Profile
        Profile.objects.create(user=instance)

        # Create and save Cloud Storage bucket, 3 retries for possible conflicts
        _retries = 1
        _create_success = False
        _processor = DocumentProcessorAbstractClass.get_cloud_processor()
        while _retries<4 and not _create_success:
            try:
                _bucket_name = get_randomized_username(
                    instance.username, get_app_setting('', 'default.bucket_name_length'), 
                    True, 
                    '-'
                )
                _create_success = _processor.create_storage(_bucket_name)
            except ClientError as e:
                logger.debug('Create storage attempt #%s failed:[bucket_name=%s]::[user_id=%s]',_retries,_bucket_name,instance.id)
                _retries += 1

        if not _create_success:
            User.objects.get(pk=instance.id).delete()
            raise InvalidCloudStorage('Error creating storage for user')
        
        instance.profile.storage_bucket=_create_success

        # Create folders for documents and email relay
        _folders = [get_app_setting('', 'cloud_processor.folders.documents'), \
                    get_app_setting('', 'cloud_processor.folders.emails')]
        _processor.create_folder(_create_success, _folders)

        p = None
        _max_relay_length = get_app_setting('', 'default.relay_length')
        _relay_email = instance.username[:_max_relay_length] \
              if len(instance.username) > _max_relay_length else instance.username
        while p is None:
            p=Profile.objects.all().filter(email_relay=_relay_email)
            _relay_email = get_randomized_username(
                instance.username, get_app_setting('', 'default.relay_length'), 
                True, 
                '.'
            )
        instance.profile.email_relay = _relay_email
        
        instance.profile.save()
    except Exception as e:
        logger.debug('[user_id=%s]',instance.id)
        logger.exception(e)
        raise e

    try:
        # Create User Stat
        s = UserStat.objects.create(
            user=instance, 
            credits_balance=100.0
        )
        s.save()
        logger.info('User Stat created::[user_id=%s]',instance.id)
    
        # Credit 100 credits to user account on Transaction Log model
        t = TransactionLog.objects.create(
            tx_type="CDT",
            tx_amt=100.0,
            auth_code="Signup reward",
            user=instance
        )
        t.save()
        logger.info('Transaction Log created for new user::[user_id=%s]',instance.id)
    except Exception as e:
        logger.debug('Error creating transaction log::[user_id=%s]',instance.id)
        logger.exception(e)
        pass # Fail silently
    

@receiver(post_save, sender=SocialAccount)
def update_user(sender, instance, created, **kwargs):
    """
    Executed when a new user account is created and saved through a social account provider. 
    The user account is updated with information from social profile
    """
    if not created:
        return
    
    user = User.objects.get(id=instance.user_id)
    try:
        user.first_name = instance.extra_data['given_name']
        user.last_name = instance.extra_data['family_name']
        user.save()
        logger.info('First and Last name updated for new user::[user_id=%s]',instance.user_id)
    except Exception as e:
        logger.debug('[user_id=%s]',instance.user_id)
        logger.exception(e)
        pass # Fail silently    


@receiver(post_save, sender=Document)
def deduct_credit(sender, instance, created, **kwargs):
    """
    Executed when a document is processed
    1. Deducts a credit from the user profile credits_balance field
    2. Adds a credit to the user profile credits_used field
    3. Increments the processed_receipt_count by 1
    4. Creates a Credit_Transaction object noting that a credit was deducted along with receipt reference

    This method raises an error if it is unable to update the profile object for some reason. 
    As this has a financial implication. However this method will silently handly any error related to 
    recording the credit transaction as this does not have a direct financial implication
    """

    if not created:
        return

    try:
        p = UserStat.objects.get(user_id=instance.user_id)
        p.credits_balance = p.credits_balance - 1
        p.credits_used = p.credits_used + 1
        p.pro_document_count = p.pro_document_count + 1
        p.save()
        logger.info('Credit deducted for user::[user_id=%s]',instance.user_id)
    except ObjectDoesNotExist as o:
        logger.debug('[user_id=%s]',instance.user_id)
        logger.exception(o)
        raise o
    except Exception as e:
        logger.debug('[user_id=%s]',instance.user_id)
        logger.error(e)
        raise e
    
    # create Credit Transaction row
    try:
        t = TransactionLog.objects.create(
            tx_type="DBT",
            tx_amt=1.0,
            user=instance
        )
        t.save()
        logger.info('Transaction logged::[user_id=%s]::[tx_type=DBT]::[tx_amt=1.0]',instance.user_id)
    except Exception as e:
        logger.debug('[user_id=%s]',instance.user_id)
        logger.error(e)
        pass
    