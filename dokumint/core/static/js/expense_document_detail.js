'use strict';

// Bind event to display receipt image when receipt image icon is clicked
$('.image-link').on('click', function (event) {
    window.open($('.image-link').attr('image-link'), '_blank');
})

/**
 * Visibly adds a document tag badge upon successfully saving the created tag in database
 */
successFns.addTagSuccess = function(response) {
    let _formaction='/api/document/{{ document.id }}/tag/' + response['id'] + '/';
    let tag = '<span class="badge text-bg-secondary" id="tag-' + response['id'] + '">' +
                response['text'] + '&nbsp;' + 
                '<a href="#" style="text-decoration: none;" class="remove-tag text-light" formaction="' + _formaction + '">x</a>' +
                '</span> ';
    $('#current-tags').append(tag);
}

/**
 * Visibly removes a document tag badge upon successfully deletion in database
 */
successFns.deleteTagSuccess = function(response) {
    let tag = '#tag-' + response['id'];
    $(tag).remove();
}

/**
 * Cleans up inline editing fields after successful server side update
 * Resets all inline editing fields and shows edit icons
 * @param {JSON} response - JSON response object after AJAX call
 */
successFns.editDocumentSummarySuccess = function(response) {
    closeModal();
    let responseHTML = response['html'];
    $('#expense-document-body').replaceWith(responseHTML);
}

/**
 * Updates receipt line item after successful edi or delete request
 * @param {JSON} response - JSON response object after AJAX call
 * @param {Object} formData - Data object containing user edits to receipt line item
 */
successFns.editLineItemSuccess = function (response) {
    closeModal();
    let lineRow = $("#expense-line-item-" + response['expense-line-item-id']);
    if (lineRow.length) {
        let dividerRow = $("#hr-" + response['expense-line-item-id']);
        dividerRow.remove();
        lineRow.replaceWith(response['html']);
    } else {
        $(response['html']).insertBefore('#add-line-item-row');
    }
}

/**
 * Remove receipt line item from display upon successful server delete
 * @param {JSON} response - AJAX response object
 */
successFns.deleteLineItemSuccess = function (response) {
    closeModal();
    let lineRow = $("#expense-line-item-" + response['expense-line-item-id']);
    lineRow.remove();
    let dividerRow = $("#hr-" + response['expense-line-item-id']);
    dividerRow.remove();
}

/**
 * Toggles receipt review status on screen after successful save in database
 * @param {JSON} response - JSON response object after AJAX call
 */
successFns.toggleReceiptReviewStatus = function (response) {
    let element = $("#badge-review-status");
    element.html(response['review_status_text']);
    if (response['review_status'] === 'true') {
        element.removeClass('text-bg-secondary').addClass('text-bg-primary');
    } else {
        element.removeClass('text-bg-primary').addClass('text-bg-secondary');
    }
}

$(document).ready(function () {
    /**
     * Toggles the edit line item form fields based on button clicked
     * @param {Element} formElement - The form to be populated
     * @param {Boolean} toggle - Flag to disable or enable fields
     */
    let toggleEditLineItemFormFields = function (modalElement, toggleEditable, mode) {
        modalElement.find("input").each(function (index, data) {
            $(this).prop("disabled", toggleEditable);
        });

        let editBtn = modalElement.find("#save-edit-line-item-btn");
        let deleteBtn = modalElement.find("#confirm-delete-line-item-btn");
        if (mode == "edit" || mode == "add") { // Reset to edit line item
            editBtn.attr('method', 'PUT');
            if (mode == "add") {
                modalElement.find(".modal-title").html("Add Line Item");
            } else {
                modalElement.find(".modal-title").html("Edit Line Item");
            }
            editBtn.show();
            deleteBtn.hide();
        } else { // Reset to delete line item
            modalElement.find(".modal-title").html("Delete Line Item");
            editBtn.hide();
            deleteBtn.show();
        }
    }

    /**
     * Populates modal form used to edit or delete receipt line item
     * @param {Element} lineItemRowElement - The line item row selected
     * @param {Element} formElement - The form to be populated
     */
    let populateEditLineItemModal = function (lineItemRowElement, modalElement, formaction) {
        let description, quantity, total = '';
        clearErrors(modalElement);
        if (lineItemRowElement != null) { // will be null if adding a new row
            description = lineItemRowElement.find('.line-item-description').text().trim();
            quantity = lineItemRowElement.find('.line-item-quantity').text().trim().substr(2);
            total = lineItemRowElement.find('.line-item-total').text().trim();
        } 
        modalElement.find('#save-edit-line-item-btn').attr('formaction', formaction);
        modalElement.find('#confirm-delete-line-item-btn').attr('formaction', formaction);
        modalElement.find("#description").val(description);
        modalElement.find("#quantity").val(quantity);
        modalElement.find("#total").val(total.replace("$", ""));
    }

    // Prepare modal for adding new line item
    $('body').on('click', '.add-line-item-btn', function (event) {
        toggleEditLineItemFormFields(editLineItemModalElement, false, 'add');
        let formaction = $(this).attr('formaction').trim();
        populateEditLineItemModal(null, editLineItemModalElement, formaction);
    });

    // Prepare modal for editing a line item
    $('body').on('click', '.edit-line-item-btn', function (event) {
        toggleEditLineItemFormFields(editLineItemModalElement, false, 'edit');
        let formaction = $(this).parent('.line-item-edit-btns').attr('formaction').trim();
        populateEditLineItemModal($(this).parents('.line-item-row'), editLineItemModalElement, formaction);
    });

    $('body').on('click', '.delete-line-item-btn', function (event) {
        toggleEditLineItemFormFields(editLineItemModalElement, true, 'delete');
        let formaction = $(this).parent('.line-item-edit-btns').attr('formaction').trim();
        populateEditLineItemModal($(this).parents('.line-item-row'), editLineItemModalElement, formaction);
    });

    // Bind event to save document review status toggle switch
    $('body').on('change', '#review-status', function(event) {
        clearErrors(mainBodyElement);
        event.data = getFormData($(event.currentTarget), csrfToken, false, true);
        if (event.data) { // If false then no edits were made
            event.onSuccess = 'toggleReceiptReviewStatus';
            event.errorPanel = mainBodyElement;
            event.method = 'PUT';
            event.url = $(event.currentTarget).attr('formaction');
            saveEditedData(event);
        }
    });

    // Save edited document summary information
    $('body').on('click', '#save-edit-document-summary-btn', function (event) {
        event.preventDefault()
        let form = $('#edit-document-summary-form');
        clearErrors(form)
        event.data = getFormData(form, csrfToken, false, true);
        console.log(event.data);
        event.errorPanel = form.find('modal-body');
        event.onSuccess = 'editDocumentSummarySuccess';
        event.url = form.attr('formaction');
        event.method = 'PUT';
        saveEditedData(event)
    });

    // Save edited line item information
    $('body').on('click', '#save-edit-line-item-btn', function (event) {
        event.preventDefault()
        let form = editLineItemModalElement.find('form');
        clearErrors(form)
        event.errorPanel = form.find('.modal-body');
        event.data = getFormData(form, csrfToken);
        event.onSuccess = 'editLineItemSuccess';
        event.url = $(event.currentTarget).attr('formaction');
        event.method = $(this).attr('method');
        saveEditedData(event)
    })

    // Process delete line item confirmation
    $('body').on('click', '#confirm-delete-line-item-btn', function (event) {
        event.preventDefault();
        let form = editLineItemModalElement.find('form');
        clearErrors(form);
        event.errorPanel = form.find('.modal-body');
        event.data = getFormData(form, csrfToken)
        event.onSuccess = 'deleteLineItemSuccess';
        event.url = $(event.currentTarget).attr('formaction')
        event.method='DELETE';
        saveEditedData(event)
    });

    // Process user creating new tag by listening for enter key
    $('input#tag-text').on('keydown',function(event) {
        if(event.keyCode == 13) {
            event.preventDefault();
            event.data = getFormData($('#add-tag-form'), csrfToken, 'tag-');
            event.onSuccess = 'addTagSuccess';
            event.url = $(this).attr('formaction');
            event.method = 'PUT';
            saveEditedData(event);
            $(event.currentTarget).val('');
        }
    });

    // Process removal of document tag
    $('body').on('click', '.remove-tag', function (event) {
        event.preventDefault();
        let tag = $(event.currentTarget).parents('.badge');
        event.onSuccess = 'deleteTagSuccess';
        event.url = $(this).attr('formaction');
        event.method = 'DELETE';
        saveEditedData(event);
    }); 

    // Download document image
    $('body').on('click', '.image-link', function (event) {
        window.open($('.image-link').attr('image-link'), '_blank');
    });
});