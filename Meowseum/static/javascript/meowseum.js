/* Description: This file is for JavaScript specific to the Meowseum project. */
  
$(document).ready(function() {
    // 2. Set up the button that changes the site from day mode to night mode. This is located in the mobile Settings modal and the desktop Layout modal.
    prepareToggleNightDayButton = function() {
        // If the user has previously toggled Day Mode on, change the Settings menu's night mode/day mode label and icon when the page loads.
        if (!settings.layout["nightModeIsOn"]) {
            $(".toggle-night-day").attr({"src":"/static/images/Sun Icon.png","alt":"Sun icon"});
            $(".toggle-night-day")[0].parentNode.firstChild.nodeValue="Day mode";
        }
        // When the sun icon or moon icon is clicked, change it and its label, change the value of the layout settings key, save it to local storage, and call the method for changing the
        // sitewide CSS.
        $(".toggle-night-day").click(function() {
            if (settings.layout["nightModeIsOn"]) {
                $(this).attr({"src":"/static/images/Sun Icon.png","alt":"Sun icon"});
                this.parentNode.firstChild.nodeValue="Day mode";
            }
            else {
                $(this).attr({"src":"/static/images/Moon Icon - White.png","alt":"Moon icon"});
                this.parentNode.firstChild.nodeValue="Night mode";
            }
            settings.toggleNightDay();
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