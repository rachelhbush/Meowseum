/* Description: Within the "settings" namespace, this script provides functions for sitewide JavaScript settings, such as changing how GIFs behave on gallery pages.
                Abstracting away sitewide changes will allow someone reading the script for a settings modal to concentrate only on the DOM changes to the modal itself.
                The main routine attaches all of the JavaScript event handlers when the page loads. All functions within this script have a numerical designation for
                where they are in its hierarchy, unless they are not invoked during the main routine.
                                
                Sections for library functions:
                A. Night mode-related functions
                B. GIF-related functions */

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
        settings.layout = {"mobileGIFsArePlaying":false, "playAllDesktopGIFs":false, "reactionToGIFMouseleave":"finish"}
        settings.update();
    }
};
createSettingsObjects();

$(document).ready(function() {
    // A. This section is for library functions related to toggling night mode CSS and images.
    //    Because this involves a page load effect, the setting information is on the back end. Updating the settings menus is handled by the AJAX response.
    settings.turnOnNightMode = function() {
        // The day mode style sheet uses the ".has-night-mode-version" class, rather than just putting day mode in the file name, in order to allow other site themes in the future.
        $("link.has-night-mode-version").each(function() {
            var path = $(this).attr("href");
            $(this).after('<link type="text/css" rel="stylesheet" href="' + path.substring(0,path.length-4) + '_night.css">')
        });
    };
    
    settings.turnOnDayMode = function() {
        $('link[href*="_night.css"]').each(function() {
            $(this).remove();
        });
    };
    
    // B. This section provides library functions affecting the behavior of <video>s on gallery pages, including the user comments page.
    // To change the GIF behavior, these are also used by buttons scripted by the mobile and desktop headers.
    // Functions with a hierarchy number are invoked by settings.prepareGIFs() sitewide when the page loads.
    
    // 1.1 Play all videos in the gallery.
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
    
    // 1.2 Play all videos. Remove any mouseover or mouseout event handlers associated with other settings.
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
    
    // 1.3.1. The GIF will loop for at least as long as the user is mousing over it. This function is invoked at the beginning of all three functions for implementing each option for mouseout
    // behavior, in order to make switching between mouseout behaviors easier.
    settings.playVideoOnMouseover = function() {
        $(".gif-container video").mouseover(function() {
            this.loop = true;
            this.play();
            // Hide the play icon while the video is playing.
            $("span", $(this).parent()).hide();
        });
    };
    
    // 1.3 When the user's cursor leaves the GIF, it finishes the current loop, goes back to the first frame, then pauses. Mouseout option A.
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
    
    // 1.4. When the user's cursor leaves the GIF, the GIF pauses. The GIF continues playing where it left off the next time the user mouses over it. Mouseout option B.
    settings.pauseVideoOnMouseout = function() {
        settings.playVideoOnMouseover();
        $(".gif-container video").mouseout(function() {
            this.pause();
            // Show the play button.
            $("span", $(this).parent()).show();
        });
    };
    
    // 1.5. When the user's cursor leaves the GIF, the video GIF loops back to the first frame and pauses. Mouseout option C.
    settings.stopVideoOnMouseout = function(){
        settings.playVideoOnMouseover();
        $(".gif-container video").mouseout(function() {
            this.currentTime = 0;
            this.pause();
            // Show the play button.
            $("span", $(this).parent()).show();
        });
    };
   
    // 1. When the page loads, make GIFs wrapped in .gif-container behave in accordance with what the user currently has under the layout settings menu.
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
   
    // 2. If the user's viewport switches between the width range for the mobile layout and the width range for the laptop/desktop layout, refresh the page.
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
   
    // 0b. Implement the user's settings. This is the second part of the main routine, after jQuery loads.
   var customizeSiteWithSettings = function () {
        settings.prepareGIFs();
        refreshWhenWidthPassesTheMobileBreakpoint();
   };
    customizeSiteWithSettings();
});