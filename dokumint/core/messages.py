from enum import Enum

from django.utils.translation import gettext_lazy as _

class ErrorMessages(Enum):
    NON_FIELD_ERROR_MSG_LABEL = _('General error')
    CATEGORY_DELETE_FAILURE = _('An error occurred while processing the deletion of your document category. Please try again or contact support if the problem persists')
    DOCUMENT_DELETE_FAILURE = _('An error occurred while processing the deletion of your document. Please try again or contact support if the problem persists')
    DOCUMENT_UPDATE_FAILURE = _('An error occurred while processing the updates to your document. Please try again or contact support if the problem persists.')
    DOCUMENT_UPLOAD_FAILURE = _('An error occurred while processing your uploaded document. Please try again or contact support if the problem persists')
    DOCUMENT_LINE_ITEM_ADD_FAILURE = _('An error occurred while processing the addition of your line item. Please try again or contact support if the problem persists')
    DOCUMENT_LINE_ITEM_DELETE_FAILURE = _('An error occurred while processing the deletion of your line item. Please try again or contact support if the problem persists')
    DOCUMENT_LINE_ITEM_UPDATE_FAILURE = _('An error occurred while processing the update of your line item. Please try again or contact support if the problem persists')
    STD_ERROR_END_1 = _('Please try again or contact support if the problem persists')
    USER_PROFILE_UPDATE_FAILURE = _('An error occurred while updating your user profile. Please try again or contact support if the problem persists')
    INVALID_EXPENSE_LINE_ITEM_DESCRIPTION = _('Description is required. Please specify a valid description')
    INVALID_EXPENSE_LINE_ITEM_QUANTITY = _('Please specify a valid quantity')
    INVALID_EXPENSE_LINE_ITEM_TOTAL = _('Please specify a valid total')