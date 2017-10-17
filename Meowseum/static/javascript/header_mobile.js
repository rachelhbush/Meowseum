$(document).ready(function() {
    // 2. The pause/play icon toggles whether the GIFs wrapped in .gif-container are playing. GIFs everywhere else on the site will always autoplay.
    preparePausePlayIcon = function() {
        var buttonSelector = "#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle";
        if (settings.mobileGIFsArePlaying()) {
            settings.mobilePlayAll();
        }
        $(buttonSelector).click(function() {
            if (settings.mobileGIFsArePlaying()) {
                settings.mobilePauseAll();
            }
            else {
                settings.mobilePlayAll();
            }
        });
    };
    
    // 1. If the search bar is hidden, clicking the magnifying glass icon brings it down. If the search bar is visible, clicking it hides it with a sliding-up animation.
    var prepareSearchIcon = function() {
        $("#portrait-smartphone-icons #search-toggle, #landscape-smartphone-or-wider-icons #search-toggle ").click(function() {
            if ($("#search-row").css("display") == "none") {
                $("#search-row").slideDown("fast");
            }
            else {
                $("#search-row").slideUp("fast");
            }
        });
    };
    
    // 0. Main function. Set up the behavior of the icon buttons in the header, aside from those which launch modals.
    var main = function() {
        preparePausePlayIcon();
        prepareSearchIcon();
    };
    main();
});