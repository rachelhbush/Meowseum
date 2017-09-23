/* File name: settings_v0_0_15.js    Version date: Author: Rachel Bush
   Version description: 
   
   File description: Within the "settings" namespace, this script provides functions for changing the sitewide CSS. It also provides functions for changing how GIFs behave on
                     gallery pages. The main routine changes the sitewide CSS when the page loads. Abstracting away sitewide changes will allow someone reading the script for a
                     settings modal to concentrate only on the DOM changes to the modal itself. All functions within this script have a designation for where they are in its
                     hierarchy, unless they are not invoked during the main routine. */

// Create a namespace for the sitewide JavaScript settings.
window.settings = window.settings || {};

// 1. After updating a value in settings.layout, this function will save it to local storage. It is one line, so its main benefit is not having to type out as much and encapsulating more
// of the process within a single file.
settings.update = function() {
   localStorage.layoutSettings = JSON.stringify(settings.layout);
};

// 0a. Load the settings from local storage or set the default settings. This is the first part of the main routine, before jQuery loads. The main routine has been split
// because settings.prepareDayModeBackground() needs to be invoked before jQuery loads, but the rest needs to be invoked after jQuery loads.
var createSettingsObjects = function() {
    // The layout settings need to be available before jQuery has loaded, so that the user will not see the background color change as the site is being customized.
    // Most pages will need the layout settings again. Keeping the layout settings as a property of a global variable will prevent them from having to be retrieved twice.
    if (localStorage.layoutSettings) {
        settings.layout = JSON.parse(localStorage.layoutSettings);
    }
    else {
        // Set the site's default layout settings. They cannot yet be saved to local storage, because their absence from local storage will be used to know that this is the
        // user's first time on the site. In that case, the device can skip the routine for checking whether anything has changed from the defaults.
        settings.layout = {"nightModeIsOn":true, "mobileGIFsArePlaying":false, "playAllDesktopGIFs":false, "reactionToGIFMouseleave":"finish"}
        settings.update();
    }
};
createSettingsObjects();

// When the page loads in day mode by removing night mode CSS, there is a slight delay while jQuery loads where the background would appear black.
// This function stops the blinking effect by changing the background color as soon as the page loads.
// It works while styling the <body>. On some pages, most of the background color is set by other elements. When those pages are loaded, <body> only affects a tiny fraction of
// leftover space on the page. During the transition, those pages need <body> to have a background color representative of the color of the page as a whole. Then when the page
// is loaded, <body> should have its usual background color for the leftover space. So, there is a second parameter in case the final <body> background color is different from
// the one used while the page is loading. Each page on this site has a <script> with only an invokation of this function, listed after all the page's libraries and CSS files,
// but before all the page's other <script>s. The parameters of the function are strings representing colors, like "rgb(240,240,240)".
settings.prepareDayModeBackground = function(transitionColor, finalColor) {
    if (!settings.layout["nightModeIsOn"]) {
        // Except for the photo page, day mode pages have the default transparent (white) background color, so the function sets a transparent background color when there are no arguments.
        if (arguments.length == 0) {
            document.write('<style>body {background-color: transparent;}</style>');
        }
        else {
            document.write('<style>body {background-color: ' + transitionColor + ';}</style>');
        }
        if (arguments.length > 1) {
            // Make <body>'s intended background color a property of the settings object, so that it can be applied at the end of turnOnDayMode()'s routine.
            settings.dayModeFinalBackgroundColor = finalColor;
        }
    }
};

$(document).ready(function() {
    // 2.1. Switch to day mode.
    settings.turnOnDayMode = function() {
        // Store the CSS as it exists with night mode on, in order to be able to put it back in case night mode is toggled back on.
        settings.$nightCSS = $("link");
        // Remove any CSS <link> with a file name containing the word "night".
        $('head [href*="night"]').remove();
        // All site icons have a day mode version and a night mode version. This is implemented using a data-day attribute for the path to the day version and a data-night attribute for
        // the path to the night version. For each image with different versions for night mode and day mode, overwrite the src attribute's value with the value of the data-day attribute.
        $("img[data-night]").each(function() {
            $(this).attr("src",$(this).data("day"));
        });
        if (settings.dayModeFinalBackgroundColor) {
            // Change over <body> from a placeholder background color it had while jQuery was loading and the page was empty.
            $("body").css("background-color",settings.dayModeFinalBackgroundColor);
        }
    };
    
   // 2. Images on the site that use different versions for day mode and night mode use data-day and data-night to store the paths to the different versions.
   // Night mode CSS is the default, so the src attribute uses the night mode version by default in order to be compatible with JavaScript being disabled. This function
   // performs the following tasks. First, when the page loads, and day mode is on, the function turns on day mode. Second, some
   // images, like the different images for the login and signup pages, are large enough that the night mode version would flash for a second before the program switches to the day mode version.
   // So, these use src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" data-night=path data-day=path, and the program gets the path string from the data- attributes.
   // This makes the image use a 1x1 transparent pixel until the JavaScript has time to work.
   // Third, the site hides the <body> by default when JavaScript is enabled, via a <style> element in base.html. This is because it takes long enough for the site's JavaScript to be ready that
   // when day mode is enabled, the user can see the night mode effects flashing for an instant before the night mode CSS is removed. The function shows the <body> when the function has
   // had a chance to get day mode ready. This still doesn't take care of the night mode background color flashing because of the delay caused by jQuery loading, which led to
   // settings.prepareDayModeBackground() needing to be invoked on almost every individual page in order to take into account how different day mode pages have different background CSS.
   //
   // With these three complications taken together, I've concluded it would be a lot easier for CSS customization to be handled server-side than client-side.
   // Other web developers trying to program night/day mode have encountered similar issues and reached the same conclusion:
   // http://stackoverflow.com/questions/40389002/how-to-use-jquery-to-implement-night-mode-without-flashing-white-on-each-page
   // I plan on moving the night mode CSS to be server-side when I have time to work on the efficiency of my site.
   var loadNightDayEffects = function() {
        if (settings.layout["nightModeIsOn"]) {
            $('img[data-night][src*="base64"]').each(function() {
                $(this).attr("src", $(this).data("night"));
            });
        }
        else {
            settings.turnOnDayMode();
        }
        // Now that the function has had its opportunity to configure the day mode CSS, show <body>, which has been hidden to prevent the user from seeing night mode effects.
        $("body").css("display","block");
   };
    
    // Switch to night mode. 
    settings.turnOnNightMode = function() {
        // Hide the body while changes are being made to the CSS, so the page user will see a blank page for a split second instead of a page with a lot of layout glitches.
        // Sometimes the user will be able to see the page without any CSS for just a few milliseconds, but because this just occurs while toggling, if I were browsing the site,
        // I wouldn't mind it.
        $("body").css("display","none");
        // Sometimes the page may have loaded in day mode and had to change the background color, and these modifications would remain after removing the style sheets.
        // Remove any modifications to background-color that have been done by JavaScript.
        $("body").css("background-color","");
        // Remove all the current style sheets. 
        $("link").remove();
        // Add back the jQuery set of CSS files that were in place before the night mode files were removed. Place them at the end of the content of <head>.
        settings.$nightCSS.appendTo("head");
        // For each image with different versions for night mode and day mode, overwrite the src attribute's value with the value of the data-night attribute.
        $("img[data-night]").each(function() {
            $(this).attr("src",$(this).data("night"));
        });
        // Without a slight delay before <body> is shown again, for some reason the script fails to hide the <body> at all while changes are being made.
        var Timer = setInterval(function() {
            $("body").css("display","block");
        },100);
    };
    
    // Toggle between day and night mode. This function also triggers the event "toggleNightDay", which excludes the toggling this script does when the page is loaded.
    // The "toggleNightDay" event is needed by some scripted elements. Rollovers can use a pair of files for day mode and a pair of files for night mode, so the background
    // matches better, and they need "toggleNightDay" to know when to refresh. The event uses the Window object, like scrolling and browser resizing.
    settings.toggleNightDay = function() {
        if (settings.layout["nightModeIsOn"]) {
            settings.layout["nightModeIsOn"] = false;
            settings.update();
            settings.turnOnDayMode();
        }
        else {
            settings.layout["nightModeIsOn"] = true;
            settings.update();
            settings.turnOnNightMode();
        }
        $(window).trigger("toggleNightDay");
    }
    
    // This section provides functions affecting the behavior of <video>s on gallery pages, including the user comments page.
    // To change the GIF behavior, these are also used by buttons scripted by mobile_header.js and laptop_desktop_header.js.
    // Functions with a hierarchy number are invoked by settings.prepareGIFs() sitewide when the page loads.
    
    // 3.1 Play all videos in the gallery.
    settings.mobilePlayAll = function() {
        $(".gif-container video").each(function() {
            this.play();
        });
    };
    
    // Pause all videos in the gallery.
    settings.mobilePauseAll = function() {
        $(".gif-container video").each(function() {
            this.pause();
        });
    };
    
    // 3.2 Play all videos. Remove any mouseover or mouseout event handlers associated with other settings.
    settings.desktopPlayAll = function() {
        $(".gif-container video").each(function() {
            // Hide the play icons while videos are playing.
            $("span", $(this).parent()).hide();
            this.play();
            // Make sure the video plays in an infinite loop, because finishLoopOnMousout() may have turned this off.
            this.loop = true;
        });
        $(".gif-container video").off("mouseover").off("mouseout");
        // Turn off the time-delayed routine within finishLoopOnMousout().
        clearTimeout(settings.resetDelay);
    };
    
    // Pause all videos. Set mouseover and mouseout event handlers for playing and pausing individual videos in the gallery.
    settings.desktopPauseAll = function() {
        $(".gif-container video").each(function() {
            $("span", $(this).parent()).show();
            this.pause();
        });
        if (settings.layout["reactionToGIFMouseleave"] == "finish") {
            settings.finishLoopOnMouseout();
        }
        else if (settings.layout["reactionToGIFMouseleave"] == "pause") {
            settings.pauseVideoOnMouseout();
        }
        else {
            settings.stopVideoOnMouseout();
        }
    };
    
    // 3.3.1. The GIF will loop for at least as long as the user is mousing over it. This function is invoked at the beginning of all three functions for implementing each option for mouseout
    // behavior, in order to make switching between mouseout behaviors easier.
    settings.playVideoOnMouseover = function() {
        $(".gif-container video").mouseover(function() {
            this.loop = true;
            this.play();
            // Hide the play icon while the video is playing.
            $("span", $(this).parent()).hide();
        });
    };
    
    // 3.3 When the user's cursor leaves the GIF, it finishes the current loop, goes back to the first frame, then pauses. Mouseout option A.
    settings.finishLoopOnMouseout = function() {
        settings.playVideoOnMouseover();
        $(".gif-container video").mouseout(function() {
            // Turn off infinite looping and calculate the time left in the video when the event happens.
            this.loop = false;
            // Calculate the amount of time remaining in the video after the user mouses out of it.
            var ms_remaining = (this.duration - this.currentTime) * 1000;
            // Wait until the amount of time remaining in the video, plus a 0.1s delay in order to give the user time to visually process the changes.
            // Bind the video in order to continue using it as the "this" object. Storing it into a variable doesn't work here because, if two videos play simultaneously, the variable's value will be overwritten. 
            settings.resetDelay = setTimeout(function() {
                // For Microsoft Edge, setting the currentTime property back to 0 doesn't reset the video back to the first frame unless the video is still playing.
                // To work around this, the script starts the video again and then pauses it. This behavior makes Google Chrome's devtools raise the following exception:
                // "Uncaught (in promise) DOMException: The play() request was interrupted by a call to pause()."
                // I assumed this is because what I'm doing is often done unintentionally, so I ignored it.
                this.play();
                this.pause();
                // Reset the video back to the first frame.
                this.currentTime = 0;
                // Show the play button.
                $("span", $(this).parent()).show();
            }.bind(this), ms_remaining+100);
        });
    };
    
    // 3.4. When the user's cursor leaves the GIF, the GIF pauses. The GIF continues playing where it left off the next time the user mouses over it. Mouseout option B.
    settings.pauseVideoOnMouseout = function() {
        settings.playVideoOnMouseover();
        $(".gif-container video").mouseout(function() {
            this.pause();
            // Show the play button.
            $("span", $(this).parent()).show();
        });
    };
    
    // 3.5. When the user's cursor leaves the GIF, the video GIF loops back to the first frame and pauses. Mouseout option C.
    settings.stopVideoOnMouseout = function(){
        settings.playVideoOnMouseover();
        $(".gif-container video").mouseout(function() {
            this.currentTime = 0;
            this.pause();
            // Show the play button.
            $("span", $(this).parent()).show();
        });
    };
   
    // 3. When the page loads, make GIFs wrapped in .gif-container behave in accordance with what the user currently has under the layout settings menu.
    // This is in the settings namespace because it must be invoked again when the GIFs undergo DOM rearrangement.
    // GIFs that were moved will have had their events detached, and they will need to be re-attached in order to play the video.
    // Having to invoke the function twice is the cost of allowing GIFs to be used across multiple types of pages. If GIFs were being used on just one
    // type of page, then the function would only have to be invoked after other procedures have completed.
    settings.prepareGIFs = function() {
        var viewportWidth = $(window).width();
        if (viewportWidth < 1200) {
            // When JavaScript moves around videos for layout purposes, videos are automatically paused, even if they have the autoplay attribute.
            // To work around this, play all GIFs when the page loads, unless the user has specified otherwise.
            if (settings.layout["mobileGIFsArePlaying"]) {
                settings.mobilePlayAll();
            }
        }
        else {
            // When the page loads, if the user previously chose to autoplay all GIFs, apply the changes again. Otherwise, attach mouseover and mouseout events.
            if (settings.layout["playAllDesktopGIFs"]) {
                settings.desktopPlayAll();
                if ($("#toggle-autoplay")[0]) {
                    // If this page doesn't have the desktop header, check that the autoplay toggling element exists in order to prevent an exception which will prevent all other JavaScript from running.
                    $("#toggle-autoplay")[0].parentNode.childNodes[0].nodeValue = "Pause all GIFs";
                }
                $("#toggle-autoplay").removeClass("glyphicon-play").addClass("glyphicon-pause");
                $("#gif-mouseout-behavior").hide();
            }
            else {
                if (settings.layout["reactionToGIFMouseleave"] == "finish") {
                    settings.finishLoopOnMouseout();
                }
                else if (settings.layout["reactionToGIFMouseleave"] == "pause") {
                    settings.pauseVideoOnMouseout();
                }
                else {
                    settings.stopVideoOnMouseout();
                }
                // This block is for when the DOM has been rearranged. If the video's Play icon is hidden, keep playing the video.
                $(".gif-container video").each(function() {
                    $gifContainer = $(this).parent();
                    if ($("span",$gifContainer).css("display") == "none") {
                        this.play();
                    }
                });
            }
        }
    };
   
    // 4. If the user's viewport switches between the width range for the mobile layout and the width range for the laptop/desktop layout, refresh the page.
    //    This is a band-aid until I get around to making JavaScript functions less dependent viewport dimensions or able to respond more to changes in viewport dimensions.
    //    Refreshing the page may turn out to be more efficient, and plenty of sites redirect to the mobile version or make the layout have a minimum width, so I'll probably
    //    just leave this as it is.
    var refreshWhenWidthPassesTheMobileBreakpoint = function() {
        viewportWidth = $(window).width();
        if (viewportWidth > 1200) {
            // If the page loaded with the laptop/desktop layout and the viewport width shrank below the breakpoint when the browser was resized or the
            // device orientation changed, refresh the page.
            $(window).on("orientationchange",function() {
                var viewportWidth = $(window).width();
                if (viewportWidth < 1200) {
                    location.reload();
                }
            });
            $(window).on("throttledresize",function() {
                var viewportWidth = $(window).width();
                if (viewportWidth < 1200) {
                    location.reload();
                }
            });
        }
        else {
            // If the page loaded with the mobile layout and the viewport width grew above the breakpoint when the browser was resized or the
            // device orientation changed, refresh the page.
            $(window).on("orientationchange",function() {
                var viewportWidth = $(window).width();
                if (viewportWidth > 1200) {
                    location.reload();
                }
            });
            $(window).on("throttledresize",function() {
                var viewportWidth = $(window).width();
                if (viewportWidth > 1200) {
                    location.reload();
                }
            });
        }
    };
   
    // 0b. Implement the user's settings.
    // This is the second part of the main routine, after jQuery loads.
   var customizeSiteWithSettings = function () {
        loadNightDayEffects();
        settings.prepareGIFs();
        refreshWhenWidthPassesTheMobileBreakpoint();
   };
    customizeSiteWithSettings();
});