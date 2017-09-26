/* Associated files: upload_page1.html, upload_page1.css, upload_page1.js */

$(document).ready(function() {
   // 1. First, while the "Up for adoption", "Lost", or "Found" button is pressed, it should hide the Submit button and replace it with a button labeled "Next page". 
   //    The page loads with the Pets button pressed, which will make the Submit button reappear if it is pressed again.
   //    Second, if the user hasn't yet filled out his or her contact information, the script will display a warning that the user must do so in order to be able to upload.
   //    When the user has submitted the form and had it returned with the error, in which case the same error will be at the top of the form instead.
    var prepareUploadType = function() {
        $('[name="upload_type"]').on("change", function() {
            // Obtain the upload type from the radio button. The upload type has to be in lower case in order to be able to use it in the tag system later.
            var $grandparent = $(this).parent().parent();
            var uploadType = $('input[type="radio"]:checked',$grandparent).val();
            // Determine whether the message that the user doesn't have contact information on record is in the template.
            
            // If the Pets button, which was originally pressed, is pressed again, make the Submit button appear and hide the More detail button.
            if (uploadType == "pets") {
                $("footer.form .btn-default, .form .modal-footer .btn-default").hide();
                $("footer.form .btn-primary, .form .modal-footer .btn-primary").show();
                
                if ($("#upload-type-field + #contact-record-warning")[0]) {
                    // Hide the warning about contact information again when the user reselects the Pets section.
                    $("#upload-type-field + #contact-record-warning").hide();
                }
            }
            // If any of the other buttons are pressed, hide the Submit button and show the More detail button in its place.
            else {
                $("footer.form .btn-primary, .form .modal-footer .btn-primary").hide();
                $("footer.form .btn-default, .form .modal-footer .btn-default").show();
                
                if ($("#contact-record-warning")[0] && !$("#contact-record-warning:visible")[0]) {
                    // When the user selects Adoption, Lost, or Found, if the user hasn't registered contact information yet, show a warning underneath the buttons.
                    // Don't show a second copy of the warning if the user has submitted the form and the warning is already being shown as an error at the top of the page.
                    $("#upload-type-field + #contact-record-warning").show();
                }
            }
        });
    };
    
    // 0. Main function
    var main = function() {
        prepareUploadType();
    };
    main();
});