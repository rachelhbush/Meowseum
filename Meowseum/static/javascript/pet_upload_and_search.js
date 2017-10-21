/* Associated files: pet_upload_and_search.css, pet_upload_and_search_night.css, pet_upload_and_search.js
   Description: This file contains all the JavaScript for searching and uploading to the Adoption, Lost, and Found categories.
*/

$(document).ready(function() {
    // 1. If the cat has multicolor or tortoiseshell fur, then hide the fields intended for other coat patterns and show the fields specifically for narrowing down this coat pattern.
    //    The adoption search menu uses a multiselect, and it will only show the fields for tortoiseshell cats if the tortoiseshell pattern is the only pattern selected.
    var prepareTricolorFields = function() {
        $('select[name="pattern"]').change(function() {
            if ($(this).val() == "tortoiseshell") {
                $(".calico-field, .tortie-tabby-field, .dilute-field").show();
                $(".color1-field, .color2-field").hide();
            }
            else {
                $(".calico-field, .tortie-tabby-field, .dilute-field").hide();
                $(".color1-field, .color2-field").show();
            }
        });
        // Set up the search menu's tricolor fields.
        $('input[type="checkbox"][name="pattern"]').change(function() {
            // Retrieve an array of the values of the checked checkboxes within the checkbox dropdown.
            var checkboxValues = $('input[type="checkbox"][name="pattern"]:checked').map(function() {
                return $(this).val();
            })
            .toArray();
            // Toggle whether or not the "Color" field is shown or the tortoiseshell cat fields are shown, based on whether "Multicolor" is the only pattern checkbox checked.
            if (checkboxValues.length == 1 && checkboxValues[0] == "tortoiseshell") {
                $("calico-field, .tortie-tabby-field, .dilute-field").show();
                $(".color-field").hide();
            }
            else {
                $("calico-field, .tortie-tabby-field, .dilute-field").hide();
                $(".color-field").show();
            }
        });
    };
    
    // 2. When the "has a collar" checkbox is checked, show the fields that are only relevant when the cat has a collar.
    var prepareHasACollarCheckbox = function() {
        var $has_a_collar_checkbox = $('input[type="checkbox"][value="has a collar"]');
        $has_a_collar_checkbox.change(function() {
            if ($(this).prop("checked")) {
                $("#collar-fieldset").collapse('show');
                $("#collar-fieldset").addClass('in');
            }
            else {
                $("#collar-fieldset").collapse('hide');
                $("#collar-fieldset").removeClass('in');
            }
        });
    };
    
    // 3. When either the microchip checkbox or the serial number tattoo is checked, show the field for the ID of a microchip or tattoo.
    var prepareMicrochipTattooIDCheckboxes = function() {
        var $microchipped_checkbox = $('input[type="checkbox"][value="microchipped"]');
        var $has_a_tattoo_of_a_serial_number_checkbox = $('input[type="checkbox"][value="has a tattoo of a serial number"]');
        $microchipped_checkbox.change(function() {
            if ($(this).prop("checked") && !$has_a_tattoo_of_a_serial_number_checkbox.prop("checked")) {
                $("#id-number-description-field").collapse('show');
                $("#id-number-description-field").addClass('in');
            }
            else {
                if (!$(this).prop("checked") && !$has_a_tattoo_of_a_serial_number_checkbox.prop("checked")) {
                    $("#id-number-description-field").collapse('hide');
                    $("#id-number-description-field").removeClass('in');
                }
            }
        });
        $has_a_tattoo_of_a_serial_number_checkbox.change(function() {
            if ($(this).prop("checked") && !$microchipped_checkbox.prop("checked")) {
                $("#id-number-description-field").collapse('show');
                $("#id-number-description-field").addClass('in');
            }
            else {
                if (!$(this).prop("checked") && !$microchipped_checkbox.prop("checked")) {
                    $("#id-number-description-field").collapse('hide');
                    $("#id-number-description-field").removeClass('in');
                }
            }
        });
    };
    
    // 0. Main function
    var main = function() {
        prepareTricolorFields();
        prepareHasACollarCheckbox();
        prepareMicrochipTattooIDCheckboxes();
    };
    main();
});