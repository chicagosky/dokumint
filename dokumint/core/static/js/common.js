'use strict';

/**
 * Defining common success functions
 */

// Toggles favorite indicator after successfully updating user favorite in db
successFns.toggleFavorite = function (response) {
    let el = $('span.favorite[document="' + response.document_id + '"]');
    let icon = el.find('i');
    if (icon.hasClass('bi-star-fill')) {
        icon.removeClass('bi-star-fill').addClass('bi-star');
    } else {
        icon.removeClass('bi-star').addClass('bi-star-fill');
    }
    let fVal = response.is_favorite ? 'False' : 'True';
    el.find('#is-favorite').val(fVal);    
}

/**
 * Clear previously displayed error messages prior to form submission
 * @param {Element} fromElement - Parent element housing current error messages; typically a modal dialog or form
 */
function clearErrors(fromElement) {
    fromElement.find('.alert-danger').each(function () {
        $(this).remove();
    });
}

/**
 * Close modal form after saving edits
 */
function closeModal() {
    $('body').find('.modal:visible').modal('hide');
}

/**
 * Just as the function's name - do nothing :)
 */
function doNothing() {
    // do nothing
}

/**
 * Converts dotted string notation to a nested JSON object
 * @param {string} path 
 * @param {*} value 
 * @param {object} obj 
 */
function stringToObj(path, value = null, obj) {
    let parts = path.split("."),
      part;
    const last = parts.pop();
    while (part = parts.shift()) {
      if (typeof obj[part] != "object") obj[part] = {};
      obj = obj[part]; // update "pointer"
    }
    obj[last] = value;
}
  
/**
 * Display validation errors in error panel
 * @param {Element} displayElement - element that will be used to display errors
 * @param {Object} errors - List of validation errors
 */
function displayErrors(displayElement, errors) {
    for (let error in errors) {
        if (typeof(errors[error]) == 'object') {
            for (const [key, value] of Object.entries(errors[error])) {
                console.log(displayElement);
                displayElement.prepend(
                    '<div class="alert alert-danger" role="alert">' +
                    key + " : " + value +
                    '</div>'
                );
            }
        } else {
            displayElement.prepend(
                '<div class="alert alert-danger" role="alert">' +
                error + " : " + errors[error] +
                '</div>'
            );
        }
    }
}

/**
 * Construct form data for AJAX 
 */
function getFormData(element, csrfToken, removePrefix=false, nestedForm=false) {
    let formData = new FormData();
    formData.append("csrfmiddlewaretoken", csrfToken);
    let document = {};
    // check if element is an input field 
    if (element.is('input')) {
        let inputId = (removePrefix) ? $(element).attr("id").replace(removePrefix, '') : $(element).attr("id");
        inputId = inputId.replaceAll('-', '_');
        
        // checkboxes need special handling due to this issue https://stackoverflow.com/a/24588399/776543
        let value = element.is(':checkbox') ? element[0].checked : element.val();
        appendData(inputId, value, formData, document, {'nestedForm': nestedForm});
    } else {
        // this is a parent element of other input fields
        // find child input fields and add data
        element.find("input").each(function (index, data) {
            let inputId = (removePrefix) ? $(this).attr("id").replace(removePrefix, '') : $(this).attr("id");
            inputId = inputId.replaceAll('-', '_');
            let value = ($(this).attr("type") == "file") ? $(this)[0].files[0] : $(this).val();
            appendData(inputId, value, formData, document, {'nestedForm': nestedForm});
        });  
    }
    if (Object.keys(document).length > 0) {
        formData.append('nested_data', JSON.stringify(document));
    } 
    return formData;
}

function appendData(inputId, value, formData, document, options) {
    if (options['nestedForm']) {
        stringToObj(inputId, value, document);
    } else {
        formData.append(inputId, value);
    }
}

/**
 * Logs user out of current session
 */
function logout() {
    document.getElementById('logout-form').submit();
    return false;
}

/**
 * Saves edits to receipt via AJAX call. 
 * Single function to save edits to individual line items
 * @param {Object} event - Event object that triggered the call to this function
 */
var saveEditedData = function (event) {
    let onSuccessFn = event.onSuccess;
    let errorPanel = (event.errorPanel) ? event.errorPanel : $('#display-errors');
    let enctype = (event.enctype) ? event.enctype : "application/x-www-form-urlencoded";
    let method = (event.method) ? event.method : "POST";
    let headers = (event.headers) ? event.headers : { 'X-CSRFToken': csrfToken };;
    $.ajax({
        cache: false,
        contentType: false,
        data: event.data,
        enctype: enctype,
        headers: headers,
        processData: false,
        type: method,
        url: event.url,
        success: function (response) {
            if (response) {
                successFns[onSuccessFn](response);
            }
        },
        error: function (response) {
            let errors = response["responseJSON"]["errors"];
            displayErrors(errorPanel, errors);
        }
    });
}

/**
 * Toggle Favorite status on user input
 */
$(window).on('load', function() {
    $('.favorite').on('click', function (event) {
        event.preventDefault();
        event.data = new FormData();
        event.data = getFormData($(event.currentTarget), csrfToken, false, true);
        event.onSuccess = 'toggleFavorite';
        event.errorPanel = mainBodyElement;
        event.method = 'PUT';
        event.url = $(event.currentTarget).attr('formaction');
        saveEditedData(event);
    });
});