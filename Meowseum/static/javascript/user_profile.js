/* Associated files: user_profile.js, user_profile_desktop.html, user_profile_desktop.css, user_profile_mobile.html, user_profile_mobile.css, user_profile_night.css */

$(document).ready(function() {
    /* 1. Set up the widgets for showing and hiding content. Prepare the dropdown in the toolbar and then the Edit buttons. */
    var prepareSections = function() {
        // Enable the dropdown in the toolbar to change the section shown underneath <main>.
        $(".dropdown-toggle.change-label+.dropdown-menu a").click(function(){
            // Retrieve the name of the section to be shown by getting it from the label of the option clicked, then turning it into all lowercase
            // with dashes between words.
            var optionLabel = $(this).text().toLowerCase();
            // Replace all spaces between words in the label with dashes.
            var pattern = / /g;
            var optionLabel = optionLabel.replace(pattern,"-");
            var newSectionID = "#" + optionLabel;
            // Hide the section being currently viewed.
            $("#user-profile-desktop section, #user-profile-mobile section").hide();
            // Show the desired section. The ID ancestor has to be used both times in order to avoid specificity problems.
            $("#user-profile-desktop " + newSectionID + ", #user-profile-mobile " + newSectionID).show();
        });
        
        // Enable clicking an Edit button within a section to show a corresponding section with an editing form.
       $("#user-profile-desktop section .edit-btn, #user-profile-mobile section .edit-btn").click(function() {
           var newSectionID = "#" + $(this).parents("section").attr("id") + "-edit";
            // Hide the section being currently viewed.
            $("#user-profile-desktop section, #user-profile-mobile section").hide();
            // Show the desired section.
            $("#user-profile-desktop " + newSectionID + ", #user-profile-mobile " + newSectionID).show(); 
       });
       // The Edit button within <main> is treated separately.
       $("#user-profile-desktop main .edit-btn, #user-profile-mobile main .edit-btn").click(function() {
            $("#user-profile-desktop section, #user-profile-mobile section").hide();
            $("#user-profile-desktop #main-edit, #user-profile-mobile #main-edit").show();
       });
       
       // When the user clicks the Save Changes or Cancel button at the end of the form, take the user back to viewing the profile section.
       // I haven't begun work on the back-end yet, but I assume the Save Changes button will simultaneously be sending the changes to the server,
       // and the page will need to refresh after it does.
       $('section[id*="edit"] input[type="submit"], section[id*="edit"] .form-buttons .btn-default').click(function() {
           if ($(this).parents("section").attr("id").search("main") == -1 ) {
               // If the editing section is not for <main>, the name of the section to show will be retrieved by removing the "-edit" suffix.
               var newSectionID = "#" + $(this).parents("section").attr("id").replace("-edit","");
               // Hide the section being currently viewed.
                $("#user-profile-desktop section, #user-profile-mobile section").hide();
                // Show the desired section. The ID ancestor has to be used both times in order to avoid specificity problems.
                $("#user-profile-desktop " + newSectionID + ", #user-profile-mobile " + newSectionID).show(); 
           }
           else {
                // If the editing section is for <main>, the name of the section to show will be retrieved from the section dropdown button's current label.
                viewportWidth = $(window).height();
                if (viewportWidth > 1200) {
                    var dropdownLabel = $("#user-profile-desktop .dropdown-toggle.change-label").text().trim().toLowerCase();
                }
                else {
                    var dropdownLabel = $("#user-profile-mobile .dropdown-toggle.change-label").text().trim().toLowerCase();
                }
                // Replace all spaces between words in the label with dashes.
                var pattern = / /g;
                var dropdownLabel = dropdownLabel.replace(pattern,"-");
                var newSectionID = "#" + dropdownLabel;
                // Hide the section being currently viewed.
                $("#user-profile-desktop section, #user-profile-mobile section").hide();
                // Show the section that was open prior to editing the main section.
                //  The ID ancestor has to be used both times in order to avoid specificity problems.
                $("#user-profile-desktop " + newSectionID + ", #user-profile-mobile " + newSectionID).show(); 
            }
       });
    };
    
    /* 2. Customize the labels of the form for editing the "About me and cats" profile section, depending on whether the user has ever owned a cat. */
    var customizeAboutMeAndCatsLabels = function() {
        $('[name="cat-ever"]').change(function() {
            var currentOrPreviousCatOwner = $('input[type="radio"][name="cat-ever"]:checked').val();
            // If the user answers "No" to "Have you ever owned a cat?"
            if (currentOrPreviousCatOwner == "no") {
                // Hide the fields relevant only to current or previous cat owners.
                $('div[id*="field"]:has([name="my-cats-info"]), div[id*="field"]:has([name="my-cats-behavior"])').hide();
                // Slightly change a question to make it relevant to non-cat owners.
                $('textarea[name="cat-story"]').prev().prev().text("Do you have any awesome stories about cats?");
            }
            else {
                // If the user changes the answer to "Have you ever owned a cat?" back to "Yes", return the form to its original state.
                $('div[id*="field"]:has([name="my-cats-info"]), div[id*="field"]:has([name="my-cats-behavior"])').show();
                $('textarea[name="cat-story"]').prev().prev().text("Do you have any awesome stories about your cats?");
            }
        });
    };
   
    
    /* 0. Main function */
    var main = function() {
        prepareSections();
        customizeAboutMeAndCatsLabels();
    }
    main();
});