/* File names: pet_upload_and_search_v0_0_3_2.js  Version date: Author: Rachel Bush
   File description: This file contains all the JavaScript for searching and uploading to the Adoption, Lost, and Found categories.
   Version description: 
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
    
    // 2. When either the microchip checkbox or the serial number tattoo is checked, show the field for the ID of a microchip or tattoo.
    var prepareMicrochipTattooIDCheckboxes = function() {
        $('input[type="checkbox"][name="microchipped"]').change(function() {
            if ($(this).prop("checked") && !$('input[type="checkbox"][name="has_serial_number_tattoo"]').prop("checked")) {
                $("#id-number-description-field").collapse('show');
                $("#id-number-description-field").addClass("in");
            }
            else {
                if (!$(this).prop("checked") && !$('input[type="checkbox"][name="has_serial_number_tattoo"]').prop("checked")) {
                    $("#id-number-description-field").collapse('hide');
                    $("#id-number-description-field").removeClass("in");
                }
            }
        });
        $('input[type="checkbox"][name="has_serial_number_tattoo"]').change(function() {
            if ($(this).prop("checked") && !$('input[type="checkbox"][name="microchipped"]').prop("checked")) {
                $("#id-number-description-field").collapse('show');
                $("#id-number-description-field").addClass("in");
            }
            else {
                if (!$(this).prop("checked") && !$('input[type="checkbox"][name="microchipped"]').prop("checked")) {
                    $("#id-number-description-field").collapse('hide');
                    $("#id-number-description-field").removeClass("in");
                }
            }
        });
    };
    
    // 0. Main function
    var main = function() {
        prepareTricolorFields();
        prepareMicrochipTattooIDCheckboxes();
    };
    main();
});