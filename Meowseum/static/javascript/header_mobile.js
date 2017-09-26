$(document).ready(function() {
    // 1.2 The pause/play icon toggles whether the GIFs wrapped in .gif-container are playing. GIFs everywhere else on the site will always autoplay.
    preparePausePlayIcon = function() {
        if (!settings.layout["mobileGIFsArePlaying"]) {
            // If the user previously paused all the GIFs before the page loaded, load the page with the default pause icon changed to a play icon.
            $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("alt", "Play Icon");
            if (settings.layout["nightModeIsOn"]) {
                $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("src", "/static/images/Play Icon - White.png");
            }
            else {
                $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("src", "/static/images/Play Icon.png");
            }
            $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").data({"night":"/static/images/Play Icon - White.png","day":"/static/images/Play Icon.png"});
        }
        $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").click(function() {
            var iconStatus = $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("alt");
            if (iconStatus == "Pause Icon")
            {
                settings.mobilePauseAll();
                settings.layout["mobileGIFsArePlaying"] = false;
                settings.update();
                $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("alt", "Play Icon");
                if (settings.layout["nightModeIsOn"]) {
                    $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("src", "/static/images/Play Icon - White.png");
                }
                else {
                    $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("src", "/static/images/Play Icon.png");
                }
                $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").data({"night":"/static/images/Play Icon - White.png","day":"/static/images/Play Icon.png"});
            }
            else
            {
                settings.mobilePlayAll();
                settings.layout["mobileGIFsArePlaying"] = true;
                settings.update();
                $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("alt", "Pause Icon");
                if (settings.layout["nightModeIsOn"]) {
                    $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("src", "/static/images/Pause Icon - White.png");
                }
                else {
                    $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").attr("src", "/static/images/Pause Icon.png");
                }
                $("#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle").data({"night":"/static/images/Pause Icon - White.png","day":"/static/images/Pause Icon.png"});
            }
        });
    };
    
    // 1.1 If the search bar is hidden, clicking the magnifying glass icon brings it down. If the search bar is visible, clicking it hides it with a sliding-up animation.
    var prepareSearchIcon = function() {
        // In the CSS, the search bar is shown so that users with JavaScript disabled can use it. I am assuming most users would prefer the search bar to be hidden by default.
        // So, hide the search bar unless the user previously decided to have it shown.
        if (settings.layout["mobileSearchBarIsHidden"]) {
            $("#search-row").hide();
        }
        $("#portrait-smartphone-icons #search-toggle, #landscape-smartphone-or-wider-icons #search-toggle ").click(function() {
            if ($("#search-row").css("display") == "none") {
                $("#search-row").slideDown("fast");
            }
            else {
                $("#search-row").slideUp("fast");
            }
        });
    };
    
    // 0. Main function. Set up the behavior of the icon buttons in the header, aside from the modals.
    var main = function() {
        prepareSearchIcon();
        preparePausePlayIcon();
    };
    main();
});