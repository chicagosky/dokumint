import logging
from django.conf import settings
from django.db import models
from django.dispatch import Signal

# Signal indicating that document line items were bulk created
bulk_created = Signal()

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class BulkCreateManager(models.Manager):
    """
    Custom Model manager that overrides the bulk_create method to send a signal upon success
    Used by DocumentLineItem Model to send a single signal after creation of all line items

    Signal includes
    sender - reference to class
    bulk_created - always set to True
    user_id - User ID associated with the create action
    item_count - number of line item rows created
    """

    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
        document_id=None,
        user_id=None
    ):
        count = len(objs)
        
        try:
            # Call super bulk create method
            list = super(BulkCreateManager, self).bulk_create(
                objs, 
                batch_size, 
                ignore_conflicts, 
                update_conflicts, 
                update_fields, 
                unique_fields
            )

            # Send bulk create signal
            bulk_created.send(
                sender=self.__class__, 
                bulk_created=True,
                document_id=document_id, 
                user_id=user_id, 
                item_count=count
            )
            logger.info('Bulk created::[item_count=%s]::[document_id=%s]::[user_id=%s]',count,document_id,user_id)
        except Exception as e:
            logger.error('Error performing bulk create::[batch_size=%s]::[user_id=%s]',batch_size,user_id)
            logger.debug('Error performing bulk create::[objs=%s]',objs)
            logger.exception(e)
            raise e

        return list  