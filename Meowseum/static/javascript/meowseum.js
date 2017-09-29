/* Description: This file is for JavaScript specific to the Meowseum project. */
  
$(document).ready(function() {
    // 2. Set up the button that toggles the site CSS theme between day mode and night mode. This is located in the mobile Settings modal and the desktop Layout modal.
    prepareToggleNightDayButton = function() {
        $(".toggle-night-day").click(function() {
            if ($("img", this).attr("alt") == "Moon icon") {
                // The moon icon indicates night mode is currently active, and clicking it turns it off.
                settings.turnOnDayMode();
                
            }
            else {
                // The sun icon indicates day mode is currently active, and clicking it turns it off.
                settings.turnOnNightMode();
            }
        });
    };
    
    // 1.1. When the user picks a file and presses OK, submit the form.
    var submitUploadOnFilePick = function() {
        // The modal content is dynamic, so the event is attached to the .modal as the closest static ancestor of the file button.
        $('#upload-menu').on("change", 'input[type="file"]', function() {
            // The element needs to be wrapped a jQuery set in order for AJAX to be able to prevent the submit event and do its own handling of form submission.
            $(this.form).submit();
        });
    };

    // 1. Set up the Upload modal's scripted form submission. 
    var prepareUploadModal = function() {
        submitUploadOnFilePick();
    };

    // 0. Main function
    var main = function() {
        if ($("#header-mobile, #header-desktop")[0]) {
            // If the page has a header, prepare header behavior used by both the mobile and desktop versions.
            prepareUploadModal();
            prepareToggleNightDayButton();
        }
    }
    main();
});