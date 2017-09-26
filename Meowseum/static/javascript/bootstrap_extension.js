/* Description: This file extends Bootstrap with extra classes and widgets that I use across all of my projects.
   The extension's JavaScript is divided into several files by topic for ease of maintenance: forms.js, settings.js, and bootstrap_extension.js for miscellaneous classes.
*/

$(document).ready(function() {
    // The first part of this file is for library functions which are under the global namespace, aside from those in forms.js, and library functions in miscellaneous namespaces.
    // Unlike the previously listed functions, they will not be invoked when the page loads.

    // 1. This jQuery plugin event is used when the script needed to wait until a single image's dimensions can be accessed.
    // It is used in place of the load() method, because a few browsers have bugs related to image dimensions, but it has the same syntax.
    // Other programmers have recommended using the .load() event on the Window object or <body>, and this has sometimes worked for me, but I was noticing on one page of my site (user comments)
    // that it would still return a height of 0 in Chrome when the images were cached.
    
    // First, Internet Explorer also ignores ignores the "load" event on cached images in all versions up until at least IE11.
    // The behavior in all other browsers is that the event happens even if the image is cached.
    // This method ensures that the load event (dimensions have loaded) will occur regardless of whether the image is cached.
    // Second, Google Chrome will sometimes fire the load() event, and sometimes it will fail to fire because it is using the cached image instead.
    // When this happens, the jQuery .width() and .height() methods will falsely return 0. The .width and .height properties will also fail to take into account any CSS styling, making them have the same values as
    // naturalWidth and naturalHeight. This is very frustrating to test, because it takes about 10 refreshes before coming across a page with cached images again.
    
    // The plugin works around these differences. Although .width and .height will still return erroneous values, it makes the .width() and .height() methods work.
    $.fn.loadImage = function(handler) {
        // This condition will be true when the image is cached.
        if (this[0].complete) {
            if (this.css("display") != "none") {
                keepCheckingForDimensions(this, handler);
            }
        }
        else {
            // Attach the load event as usual. jQuery already will make it inherit the "this" object.
            this.load(handler);
        }
    };

    // 1.1. Every 50 milliseconds, check if the image dimensions have loaded. Call the event handler when they have loaded.
    var keepCheckingForDimensions = function($image, handler) {
        if ($image.height() == 0) {
            var Timer = setTimeout(function() {
                // Do nothing for 50 milliseconds.
                keepCheckingForDimensions($image, handler);
            }, 50);
        }
        else {
            clearTimeout(Timer);
            // Invoke the callback while making it inherit the "this" object.
            handler.call($image[0]);
        }
    }

    // 2. This function defines an event that fires immediately if a video's dimensions are loaded, and it waits until they are loaded if they haven't loaded yet.
    // This makes video behavior more consistent with the .load() event traditionally used by images and other elements. The built-in event, loadedmetadata, only fires when the video's dimensions become available.
    $.fn.loadVideo = function(handler) {
        if (this.css("display") != "none" && this.height() == 0) {
            this.on("loadedmetadata", handler);
        }
        else {
            handler.call(this[0]);
        }
    };

    // 0. This function serves as a shortcut for making sure an element's dimensions are loaded when it may be either an image or video.
    $.fn.loadMedia = function(handler) {
        if (this[0].tagName == 'IMG') {
            this.loadImage(handler);
        }
        else {
            if (this[0].tagName == 'VIDEO') {
                this.loadVideo(handler);
            }
        }
    }

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    // 1.1 Use the iphone-inline-video library to enable the playsinline attribute, which prevents the iPhone from going fullscreen when touched, on iOS 8 and iOS 9.
    // Allow all iOS 8 and iOS 9 devices to autoplay videos with the muted attribute.
    var improveiOSVideoSupport = function() {
         $('video:not([muted])').each(function () {
         	enableInlineVideo(this);
         });
         $('video[muted]').each(function () {
         	enableInlineVideo(this, {
                iPad: true
            });
         });
    }

    // 1.2. For <video>s that are not descendants of <a>, the script will play and pause the video when the user clicks or touches the video.
    // This way, if the page has a GIF intended to autoplay, and the browser does not support autoplay, the user will always have some recourse to get it to play.
    // Until I create custom controls, this function also shows the default controls for the video when the video is paused so the user will know it is a video and not an image.
    var makeTouchingNonlinkVideosTogglePlaying = function() {
        $("video:not(a video)").click(function() {
            if (this.paused) {
                this.play();
            }
            else {
                this.pause();
            }
        });
        // The controls won't be shown by default in the HTML source code. In order to take into account varying mobile support for autoplay, use separate play/pause events for showing the controls.
        $("video:not(a video)").on("play", function() {
            this.controls=false;
        });
        $("video:not(a video)").on("pause", function() {
            this.controls=true;
        });
    };

    // 1.3. Use data-autoplay on all videos with sound on pages with more than one copy in the DOM, for the sake of responsiveness. data-autoplay is a Boolean attribute that indicates the video should only be
    // autoplayed when the page loads if it is visible when the page loads. This prevents the videos' audio tracks starting to play over one another. The custom attribute isn't necessary if the video
    // doesn't have an audio track or doesn't autoplay. In the future, this attribute can also be used for a client-side setting for whether or not the user wants video with audio to be able to autoplay.
    var enableCustomAutoplay = function() {
        $("video[data-autoplay]:visible").each(function() {
            this.play();
        });
    };

    // 1. Mobile devices have varying support for aspects of the <video> element. This function enhances support for <video> where possible. See the comments on the individual functions for details.
    var improveVideoSupportOnMobileDevices = function() {
        improveiOSVideoSupport();
        makeTouchingNonlinkVideosTogglePlaying();
        enableCustomAutoplay();
    };

    // 2. This function automates rollovers that work through using separate elements for the default content and the rollover content within the parent element. 
    // It hides the .default-content class on mouseenter of the parent element and shows the element with the .rollover-content class within the same parent element.
    var automaticRolloverEffects = function() {
        $(document).on("mouseenter", ":has(> .default-content)", function() {
            $(".default-content", this).hide();
            $(".rollover-content", this).show();
        });
        $(document).on("mouseleave", ":has(> .default-content)", function() {
            $(".rollover-content", this).hide();
            $(".default-content", this).show();
        });
    };

    // 3. Bootstrap allows implementing collapsible content quickly in the HTML using attributes and classes. These go on the element which you click to toggle whether another is shown,
    //    as well as the target element. By default, these use a slide-down/slide-up animation. This function extends this system by allowing elements to be hidden or shown instantly.
    //    This function also allows links to have a - at the end that will be shown whenever the collapsible is expanded.
    
    //    The HTML on the clicked element is data-toggle="instant-collapse" (the traditional slide-up uses data-toggle="collapse") and data-target="#ID".
    //    The HTML on the target element is class="collapse", which hides the target when the page loads, and id="ID". If the target is shown when the page loads, use class="collapse in".
    //    In this case, it has no effect, but it makes the HTML consistent with the case where a slide animation is being used, and helps identify the visibility of the element in the structure.
    var improveCollapsibles = function() {
        $('[data-toggle="instant-collapse"]').mousedown(function() {
            var targetID = $(this).data("target");
            $(targetID).toggle();
        });
        
        $('a[data-toggle*="collapse"]:has(.minus)').each(function() {
            var targetID = $(this).data("target");
            /* Show the - at the end of the link if the collapsible is visible when the page loads. */
            if (!$(targetID).hasClass("in")) {
                $(".minus", $(this)).hide();
            }
            $(this).click(function() {
                /* Show or hide the - when the link is clicked. */
                $(".minus", $(this)).toggle()
            });
        });
    };
    
    // 4. This function removes focus from Boostrap buttons after they are clicked. In the default, after a user clicks, it looks like the button stays pressed until the user clicks somewhere else.
    //    The only time you would want a button to appear pressed until the user clicks somewhere else is for a button that launches a small menu where you click anywhere outside it to exit, like
    //    a dropdown or a Bootstrap popover. There, the pressed state serves a purpose: indicating ongoing interaction. The function makes exception for these situations.
     
    //    For most buttons in the real world, like elevator buttons, they return to their original status immediately; the interaction is instantaneous. For most buttons on the site, like Like buttons,
    //    this is also the case. This function doesn't affect using the .active class to keep the button pressed, thereby indicating a choice or ongoing state. Throughout this site, focus after clicking
    //    was inconsistent until I added this function. In button event handlers, adding classes to the button or hiding/showing elements would remove focus, and I didn't care to add it back.
    
    //    I wrote this function instead of editing bootstrap.js because I want to keep using the CDN, in case users already have it in their cache.
    var keepBootstrapButtonsFromSticking = function() {
        $(".btn").click(function() {
            if (!$(this).is('[data-toggle="dropdown"],[data-toggle="popover"]')) {
                $(this).blur();
            }
        });
    }
    
    // 5. Modals on this site are, by default, vertically centered. If the modal is tall enough that it is going to overflow the viewport, it should stop being centered and scroll from the top instead.
    //    Exemptions from this function:
    //    1. If the modal has JavaScript that can expand the modal enough for it to overflow, then even if it starts off smaller than the viewport, it's better off starting in the scrolling position.
    //       Exempt those modals by including adding .scrollable to .modal-dialog in its HTML.
    //    2. Sidebar modals
    var calculateModalCenteringBreakpoint = function() {
        // Wait for everything on the page to load before proceeding. To calculate the dimensions of the modal, the browser needs to have calculated the dimensions of images within it, which
        // may not be present until the images are done loading. This stopped modals from not being centered every other page refresh.
        $(window).load(function() {
            var viewportHeight = $(window).height();
            $(".modal:not(.scrollable)").each(function() {
                // Store the modal into a variable so that it can be referenced by the browser resize handler.
                var $modal = $(this);
                // The height of a hidden element can't be accessed by JavaScript. The modal will be invisible when "shown" due to how Bootstrap scripts it. The z-index is set to -1 so that elements will still be
                // clickable while the height is being calculated.
                $modal.show().css("z-index","-1");
                var modalHeight = $(".modal-dialog",this).height();
                $(this).hide().css("z-index","");
                // If there isn't enough room for the modal and 10px of space with the edge of the viewport above and below the modal, then reposition the modal. Exempt modals being used as left-sidebars.
                if (modalHeight + 20 >= viewportHeight && $(".modal-dialog",this).css("margin-left") != "0px") {
                    $modal.addClass("scrollable");
                }
                $(window).on("throttledresize",function() {
                    // When the user resizes the browser, check the positioning again. Sometimes I make modals a sidebar under a certain viewport height, so check to exempt modals used as sidebars again.
                    viewportHeight = $(window).height();
                    if (modalHeight + 20 >= viewportHeight && $(".modal-dialog",$modal).css("margin-left") != "0px") {
                        $modal.addClass("scrollable");
                    }
                    else {
                        $modal.removeClass("scrollable");
                    }
                });
            });
        });
    };
    
    // 6. This function makes the .change-label class work. It makes a Bootstrap dropdown button's label change to the option that the user last selected.
    //    This makes it behave like a <select> dropdown, but with Bootstrap button shading.
    //    In the HTML, use this function by giving the dropdown's <button> the .change-label class.
    var changeBootstrapDropdownLabel = function() {
        $(".dropdown-toggle.change-label+.dropdown-menu a").click(function() {
            var optionText = $(this).text();
            var $btngroup = $(this).parent().parent().parent();
            $(".btn",$btngroup).html(optionText + ' <span class="caret"></span>');
        });
    };
    
    // 7. If a modal contains an element that toggles another modal, then dismiss the modal currently open, then open the other modal. If a link has data-toggle="modal-sm", then under 768px viewport
    //    width the link opens as usual. At 768px or wider, the link opens a modal instead. This works using any other Bootstrap range, or a number as in "-600", as a suffix.
    var responsiveModalLinks = function() {
        $('[data-toggle*="modal"]').click(function(e) {
            var viewportWidth = $(window).width();
            // Detect whether the element is in a modal by inspecting whether it has .modal as an ancestor.
            var elementIsInAModal = false;
            if ($(this).closest(".modal")[0]) {
                elementIsInAModal = true;
            }
            var elementIsALink = false;
            if ($(this).is("a")) {
                var elementIsALink = true;
                var value = $(this).data("toggle");
                var index = value.indexOf("-");
                var minModalOpeningWidth = value.substring(index + 1, value.length);
                // This should be a string like "sm" or "768".
                if (minModalOpeningWidth == "lsph") {
                    var minModalOpeningWidth = 544;
                }
                else if (minModalOpeningWidth == "sm") {
                    var minModalOpeningWidth = 768;
                }
                else if (minModalOpeningWidth == "md") {
                    var minModalOpeningWidth = 992;
                }
                else if (minModalOpeningWidth == "lg") {
                    var minModalOpeningWidth = 1200;
                }
                else if (minModalOpeningWidth == "xl") {
                    var minModalOpeningWidth = 1800;
                }
                else {
                    var minModalOpeningWidth = parseInt(minModalOpeningWidth);
                }
                if (viewportWidth >= minModalOpeningWidth) {
                    // Prevent the link from opening another page.
                    e.preventDefault();
                }
            }
            // If the element is in a modal, and the element isn't a link that opens to another page, then exit the current modal and open a new one.
            // The link part of the condition prevents the modal from distractingly being opened during the second the user is waiting for the next page to open.
            if (elementIsInAModal && (!elementIsALink || viewportWidth >= minModalOpeningWidth)) {
                var $modal = $(this).closest(".modal");
                $modal.modal("hide");
                var $target = $($(this).data("target"));
                $target.modal();
                // While a modal is shown, the .modal-open class on <body> keeps the page from scrolling and allows the modal to scroll instead.
                // If a modal is being hidden and another is immediately opened, the conflict prevents the class from being added.
                // The conflict can only be prevented by waiting to add .modal-open to <body> until the second modal's CSS transition animations are complete.
                $target.on("shown.bs.modal",function() {
                    $("body").addClass("modal-open");
                });
            }
            // The function does nothing if the value is "modal" and the element isn't in a modal.
        });
    };

    // 0. Main function
    var main = function() {
        improveVideoSupportOnMobileDevices();
        automaticRolloverEffects();
        improveCollapsibles();
        keepBootstrapButtonsFromSticking();
        calculateModalCenteringBreakpoint();
        changeBootstrapDropdownLabel();
        responsiveModalLinks();
    }
    main();
});