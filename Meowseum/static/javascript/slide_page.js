/* Associated files: slide_page.html, slide_page_author_box.html, slide_page.js, slide_page.css, slide_page_night.css */

$(document).ready(function() {
    // 1.1.1 When the user gestures to go back, redirect to the previous page in the results list.
    var navigateBack = function() {
        // Obtain the path from the arrow links in the desktop layout, which use data passed from the view via cookies.
        link = $('#slide-desktop a[class~="glyphicon-menu-left"]').prop("href");
        if (link) {
            // If there isn't an arrow present in the desktop layout, then the value of link will be undefined and invalidate the condition.
            // If there is an arrow present in the desktop layout, then redirect to its link.
            location.assign(link);
        }
    };
    // 1.1.2 When the user gestures to go forward, redirect to the next page in the results list.
    var navigateForward = function() {
        // Obtain the path from the arrow links in the desktop layout, which use data passed from the view via cookies.
        link = $('#slide-desktop a[class~="glyphicon-menu-right"]').prop("href");
        if (link) {
            // If there isn't an arrow present in the desktop layout, then the value of link will be undefined and invalidate the condition.
            // If there is an arrow present in the desktop layout, then redirect to its link.
            location.assign(link);
        }
    };
    // 1.1 Swipe left to go to the previous page, and swipe right to go to the next page in the gallery queue.
    var swipeAnywhere = function() {
        $("#swipe-back").off("swipeleft",navigateBack);
        $("#swipe-forward").off("swiperight",navigateForward);
        // Touches ignore the transparent overlays.
        $("#swipe-back, #swipe-forward").css("display","none");
        $(window).on("swipeleft",navigateBack);
        $(window).on("swiperight",navigateForward);
    };
    // 1.2. Narrow transparent overlays on the left and right sides of the viewport allow the user to navigate.
    // The user is taken back if he or she swipes in the left direction on the left side. The user is taken forward if he or she swipes in the right direction on the right side.
    // The center of the viewport remains available for horizontal scrolling. This is used when the image is a panorama or zoomed-in from portrait mode.
    // If the user zooms in, scrolls from the left side of the image to the right side, and zooms back out, then the swiping directions will be opposite the scrolling directions
    // and this will reduce the chance of accidentally triggering the wrong gesture.
    var swipeOnSides = function() {
        $(window).off("swipeleft",navigateBack);
        $(window).off("swiperight",navigateForward);
        $("#swipe-back, #swipe-forward").css("display","block");
        $("#swipe-back").on("swipeleft",navigateBack);
        $("#swipe-forward").on("swiperight",navigateForward);
    };
    // 1. Determine the swiping interface that should be used when the page is loaded. If the device is in portrait mode or in landscape mode and the image 
    // is not a panorama, use the "left for back, right for forward" interface. If the device is in landscape and the image is a panorama, use swiping on either side.
    var pageLoadSwipingAreas = function() {
        if (isPanorama && viewportWidth > viewportHeight) {
            swipeOnSides();
        }
        else {
            swipeAnywhere();
        }
    }
    
    // 2. Allow double-tapping the image to zoom in and out. The user then has to scroll to see all of the image. Most websites only use 100% width on the landscape version.
    // This feature is useful for infographics, a vertically stacked series of images, and panoramas. It lets the user "see the big picture" before scrolling down tall images.
    // If night mode is enabled, the browser makes the X icon black and semitransparent when in landscape mode or zoomed in from portrait mode.
    // The browser will change the X icon back to being opaque and nearly white when the orientation switches back to the portrait, zoomed-out state.
    var prepareImageZoom = function() {
        var zoomedIn = false;
       // 2.1.1 Zoom in. In portrait mode, this makes it up to 100% of the height of the viewport. In landscape mode, this makes it take up to 100% of the width of the viewport.
       // The other dimension is free to expand. For portrait mode, this requires putting the image in a horizontal overflow (the same one used for landscape panoramas in the default,
       // zoomed out CSS).
       // Technically, if the image is longer than the phone along the same direction it is being held (longer vertically for portrait, longer horizontally for landscape), this makes
       // the image zoom out.
        var zoomIn = function() {
            // Retrieve the viewport dimensions. This has to be done locally, because jQuery Mobile causes the values to be switched on orientationchange.
            viewportWidth = $(window).width();
            viewportHeight = $(window).height();
            if (viewportWidth < viewportHeight) {
                $("#slide-overflow-mobile > img").css({"width":"auto","height":"100vh"});
                if (settings.layout["nightModeIsOn"]) {
                    $("#landscape-order-switcher a.close").css({"opacity":0.2,"color":"black"});
                    $("#landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:active").css({"opacity":0.5,"color":"black"});                  
                }
                swipeOnSides();
            }
            else {
                $("#slide-overflow-mobile > img").css({"height":"auto","width":"100vw"});
                // If the image is a panorama, it stops being horizontally scrollable when you zoom in, so the swipe-anywhere interface is now appropriate.
                // Otherwise, the device should already be using the swipe-anywhere interface.
                if (isPanorama) {
                    swipeAnywhere();
                }
            }
            // Landscape mode and zoomed-in portrait mode always have the heading below the image in order to free up valuable viewport space "above the fold". Flexboxes are used to
            // switch the order without altering the HTML.
            $("#landscape-order-switcher").css({"display":"flex","flex-wrap":"wrap","border-bottom":"1px solid rgb(180,180,180)"});
            if (settings.layout["nightModeIsOn"]) {
                $("#landscape-order-switcher").css({"border-bottom":"1px solid rgb(70,70,70)"});
            }
            else {
                $("#landscape-order-switcher").css({"border-bottom":"1px solid rgb(180,180,180)"});
            }
            $("#landscape-order-switcher > img").css({"order":"1"});
            $("#landscape-order-switcher > h1").css({"order":"2","margin-left":"auto","margin-right":"auto"});
            // In some situations, these properties will already be on or aren't currently needed (like the landscape mode doesn't need an x-overflow at 100% width). While programming
            // this, I ran into difficulties with what CSS properties were left on an which were left off after which events, and I realized it was simpler to make sure all of these were
            // turned on together.
            $("#slide-overflow-mobile").css({"overflow-x":"auto"});
            zoomedIn = true;
        };
        // 2.1.2 Return the image back to the original CSS.
       // Technically, if the image is longer than the phone along the same direction it is being held (longer vertically for portrait, longer horizontlly for landscape), this makes
       // the image zoom back in.
        var zoomOut = function() {
            // Retrieve the viewport dimensions. This has to be done locally, because jQuery Mobile causes the values to be switched on orientationchange.
            viewportWidth = $(window).width();
            viewportHeight = $(window).height();
            if (viewportWidth < viewportHeight) {
                $("#slide-overflow-mobile > img").css({"width":"100vw","height":"auto"});
                $("#landscape-order-switcher").css({"display":"block","border-bottom":"none"});
                if (settings.layout["nightModeIsOn"]) {
                    $("#landscape-order-switcher a.close, #landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:active").css({"opacity":1,"color":"rgb(240,240,240)"});                    
                }
                swipeAnywhere();
            }
            else {
                $("#slide-overflow-mobile > img").css({"height":"100vh","width":"auto"});
                if (isPanorama) {
                    swipeOnSides();
                }
            }
            zoomedIn = false;
        };
        // 2.1 Toggle the zooming through some gesture. Currently the gesture is tapping the screen. This should be replaced later, because it would be accidentally triggered when users
        // swipe left or right to navigate between pages.
        $("#slide-overflow-mobile > img, #slide-overflow-mobile > video").on("click", function() {
            if (zoomedIn) {
                zoomOut();
            }
            else {
                zoomIn();
            }
        });
        // 2.2 Return to the zoomed-out view by setting the original CSS.
        $(window).on("orientationchange",function(e) {
            // The orientation changed from landscape to portrait while the user may have had the image zoomed in.
            if (e.orientation == "portrait") {
                $("#slide-overflow-mobile > img").css({"width":"100vw","height":"auto"});
                $("#landscape-order-switcher").css({"display":"block","border-bottom":"none"});
                if (settings.layout["nightModeIsOn"]) {
                    $("#landscape-order-switcher a.close, #landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:active").css({"opacity":1,"color":"rgb(240,240,240)"});                    
                }
                swipeAnywhere();
            }
            // The orientation changed from portrait to landscape while the user may have had the image zoomed in.
            else {
                $("#slide-overflow-mobile > img").css({"height":"100vh","width":"auto"});
                $("#slide-overflow-mobile").css({"overflow-x":"auto"});
                $("#landscape-order-switcher").css({"display":"flex","flex-wrap":"wrap"});
                $("#landscape-order-switcher > img, #landscape-order-switcher > video").css({"order":"1"});
                $("#landscape-order-switcher > h1").css({"order":"2","margin-left":"auto","margin-right":"auto"});
                if (settings.layout["nightModeIsOn"]) {
                    $("#landscape-order-switcher a.close").css({"opacity":0.2,"color":"black"});
                    $("#landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:hover, #landscape-order-switcher a.close:active").css({"opacity":0.5,"color":"black"});
                    $("#landscape-order-switcher").css({"border-bottom":"1px solid rgb(70,70,70)"});
                }
                else {
                    $("#landscape-order-switcher").css({"border-bottom":"1px solid rgb(180,180,180)"});
                }
                if (isPanorama) {
                    swipeOnSides();
                }
                else {
                    swipeAnywhere();
                }
            }
            zoomedIn = false;
        });
    };
    // 3. If the user is on a mobile, 4:3 device in landscape mode, and the video is only slightly wider than the viewport, it annoyingly shows only just a sliver of the page.
    // Showing more of the page isn't useful unless the user can see the whole heading beneath the video. If needed, this function generates thin horizontal black bars using
    // the remaining space.
    var prepareVideo = function(viewportWidth, viewportHeight) {
        // 3.1 Get the black bar CSS ready.
        var getBlackBarsReady = function() {
            var videoHeight =  $("#slide-overflow-mobile video").height();
            var headingHeight = $("#landscape-order-switcher h1").height();
            // jQuery Mobile makes the width and height switch places on orientationchange, so retrieve the viewport height again to be sure its value is correct.
            viewportHeight = $(window).height();
            var leftoverHeight = viewportHeight - videoHeight;
            if (headingHeight > leftoverHeight) {
                $("#slide-overflow-mobile").css({"background-color":"black","padding-top":leftoverHeight/2,"padding-bottom":leftoverHeight/2});
                $(window).on("orientationchange",function(e) {
                    if (e.orientation == "portrait") {
                        $("#slide-overflow-mobile").css({"background-color":"transparent","padding-top":0,"padding-bottom":0});
                    }
                    else {
                        $("#slide-overflow-mobile").css({"background-color":"black","padding-top":leftoverHeight/2,"padding-bottom":leftoverHeight/2});
                    }
                });
            }
            else {
                // If the page loaded in portrait, the original orientationchange event hasn't been overriden. This keeps the browser from checking for the need for black bars again if
                // the user switches from portrait to landscape to portrait and back to landscape.
                needForBlackBarsHasBeenChecked = true;
            }
        };
        // If the page loads in landscape mode, get the black bar CSS ready. If the page loads in portrait mode, get the black bar CSS ready the first time the user changes into landscape.
        if (viewportWidth > viewportHeight) {
            // Wait for the video dimensions to load. This isn't done when the page loads in portrait mode and orientationchanges to landscape because if the dimensions have
            // already loaded, the event won't fire.
            $("#slide-overflow-mobile video").on("loadedmetadata", function() {
                getBlackBarsReady();
            });
        }
        else {
               var needForBlackBarsHasBeenChecked = false;
               $(window).on("orientationchange",function(e) {
                    if (e.orientation == "landscape" && !needForBlackBarsHasBeenChecked) {
                        getBlackBarsReady();
                    }
                });
        }
    };

    // 4.1 This function detects if the slide needs to be stretched, and if necessary, stretches it.
    //     It performs all of the work for optimizeDesktopSlide() and it is called during certain events.
   var determineSlideCSS = function(slideWidth, slideHeight, slideSelector) {
        // First, find the dimensions of the available space for the slide -- the width of the whole section, minus 100px for the arrows.
        var availableWidth = $("#slide-container").width() - 100;
        var availableHeight = $(window).height();
        if (slideWidth < availableWidth && slideHeight < availableHeight) {
            var slideAspectRatio = slideWidth / slideHeight;
            var spaceAspectRatio = availableWidth / availableHeight;
            if (slideAspectRatio <= spaceAspectRatio) {
                // Stretch the height.
                $(slideSelector).css({"max-width":"","max-height":"none","width":"","height":"100vh"});
            }
            else {
                // Stretch the width.
                $(slideSelector).css({"max-width":"none","max-height":"","width":"calc(-100px + 100%)","height":""});
            }
        }
        // If both dimensions of the available space shrink below both natural dimensions of the slide, remove all JavaScript-added CSS. 
        else {
            $(slideSelector).css({"max-width":"","max-height":"","width":"","height":""});
        }
   };
    
    // 4. Stretch a slide that is both shorter and narrower than the available space, until its width or height is the same as that of the available space.
    //    This couldn't be done in the style sheet without affecting the CSS rules that make slides taller or wider than the available space shrink to fit it.
    //      
    //    While the slide is loading, the user will briefly see the smaller version of it. If this turns out to be distacting when clicking through a lot of slide quickly, I'll hide the slide until it is loaded.
    var optimizeDesktopSlide = function(slideWidth, slideHeight, slideSelector) {
        determineSlideCSS(slideWidth, slideHeight, slideSelector);
        // Whenever the browser dimensions change, the slide may have grown wider than the available space, so the script needs to determine the slide CSS again.
        $(window).on("throttledresize", function() {
            determineSlideCSS(slideWidth, slideHeight, slideSelector);
        });
    };
    
    // 5.1.1 Enter fullscreen mode. See the CSS file for comments on the elements and classes involved.
    var enterFullscreen = function() {
        var i = $("#fullscreen-version")[0];
        if (i.requestFullscreen) {
        	i.requestFullscreen();
        } else if (i.webkitRequestFullscreen) {
        	i.webkitRequestFullscreen();
        } else if (i.mozRequestFullScreen) {
        	i.mozRequestFullScreen();
        } else if (i.msRequestFullscreen) {
        	i.msRequestFullscreen();
        }
    };
    // 5.1.2 Leave fullscreen mode.
    var leaveFullscreen = function() {
        if (document.exitFullscreen) {
        	document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
        	document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
        	document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
        	document.msExitFullscreen();
        }
    };
    // 5.1.3 Add or remove the fullscreen class from the <div>.
    var toggleFullscreenClass = function() {
        $("#fullscreen-version").toggleClass("fullscreen");
    };
    
    // 5.1 Now that it is known the browser has the fullscreen API, attach event handlers for entering and leaving fullscreen.
    var fullscreenMode = function(slideSelector) {
        // Indicate that the image can be enlarged by changing the cursor.
        $(slideSelector).toggleClass("zoomable");
        // Fall back to "full viewport mode" if the user has disabled fullscreen or an error occurs with it.
        document.addEventListener("fullscreenerror", fullViewportMode);
        document.addEventListener("webkitfullscreenerror", fullViewportMode);
        document.addEventListener("mozfullscreenerror", fullViewportMode);
        document.addEventListener("MSFullscreenError", fullViewportMode);
        // Whenever the browser makes the <div> fullscreen or leaves fullscreen mode, including pressing F11 after having clicked it, add or remove its fullscreen class.
        document.addEventListener("fullscreenchange", toggleFullscreenClass);
        document.addEventListener("webkitfullscreenchange", toggleFullscreenClass);
        document.addEventListener("mozfullscreenchange", toggleFullscreenClass);
        document.addEventListener("MSFullscreenChange", toggleFullscreenClass);
        $(slideSelector).click(enterFullscreen);
        $("#fullscreen-version").click(leaveFullscreen);
    };

    // 5.2 Show the image with its edges touches the edges of the viewport, centered against a black background.
    var fullViewportMode = function(slideWidth, availableWidth, availableHeight, slideSelector) {
        // Find the slide CSS height, because if it is equal to the available height, then height is the limiting factor for the slide and it doesn't need to be enlarged.
        var slideCSSHeight = $(slideSelector).height();
        // Detect if the CSS rules caused the slide to shrink from its natural width to fit in the available space. In the layout, it can already take up the full height.
        if (slideWidth > availableWidth && slideCSSHeight < availableHeight) {
            // Indicate that the image can be enlarged by changing the cursor.
            $(slideSelector).toggleClass("zoomable");
            $(slideSelector).click(function() {
               // Show the image as large as possible while fitting it all in the viewport at once, centered against a black background.
               // It shows #fullscreen-version, but with the image fitting against the edges of the viewport instead of the screen.
                $("#fullscreen-version").toggleClass("fullscreen");
                $("#fullscreen-version").css({"display":"block", "position":"fixed", "top":"0px", "left":"0px","z-index":"50000"});
            });
            $("#fullscreen-version").click(function() {
                $(this).toggleClass("fullscreen");
                $(this).css({"display":"", "position":"", "top":"", "left":"","z-index":""});
            });
        }
    };
    
    // 5. If the user's browser has the fullscreen API, and the image can be enlarged further with it, allow clicking the photo to go fullscreen and clicking the photo again to exit it.
    //    If the browser doesn't support the fullscreen API, or the user has disabled it, fall back to using "full viewport mode" if it will enlarge the slide.
    //    Like fullscreen mode, "full viewport mode" will show it centered in the viewport against a black background.
    
    //    The fullscreen and "full viewport" features are enabled only if the viewport is >1200px, because mobile devices support the fullscreen API very poorly,
    //    and in the mobile layout, the image already takes up nearly all the viewport.
       
    //    The fullscreen API is only useful for when a user is clicking a photo or video to enlarge it, but not anything else.
    //    It can't be used for a slideshow mode in which the user clicks something to enable fullscreen browsing, continues to navigate to other pages, then clicks something else to exit it,
    //    as if the user pressed F11. First, whenever the user clicks a link, the fullscreen mode will exit. Second, Chrome only allows activating fullscreen via some user action, so it
    //    displays an error in the console if you use the requestFullscreen attribute outside events that the user definitely intended to activate. You can't go full-screen just by loading
    //    a page. It won't work for onmouseenter or onmousemove, or any other event I tried as workaround. I tried using jQuery's trigger() method to try to trick the browser into thinking
    //    the user had clicked when the page loads, but it didn't work, which I speculate is because the effect is the same as invoking the event handler directly.
    //    I tried triggering fullscreen mode from a link to this page, or redirecting to this page, and what happens after either is it makes the browser exit full-screen mode.
    var fullMode = function(slideWidth, slideHeight, slideSelector) {
        // Find the dimensions of the available space for the slide -- the width of the whole section, minus 100px for the arrows.
        var availableWidth = $("#slide-container").width() - 100;
        var availableHeight = $(window).height();
        // Check if the browser allows enabling fullscreen mode with JavaScript.
        if (document.fullscreenEnabled || document.webkitFullscreenEnabled || document.mozFullScreenEnabled || document.msFullscreenEnabled) {
            // If the CSS rules caused the slide to shrink from its natural dimensions to fit in the available space
            if (slideWidth > availableWidth || slideHeight > availableHeight) {
                fullscreenMode(slideSelector);
            }
        }
        else {
            fullViewportMode(slideWidth, availableWidth, availableHeight, slideSelector);
        }
    };
    
    // 6.1 Switch between the Share section and Comments section. If the user clicks the Comment button while already on the Comment section, it focuses the cursor on the
    // Reply textarea instead.
    var prepareMainSections = function(viewportWidth) {
        // This flag variable will be used to know when a section is already open. The name of the section is used instead of true or false in case more sections are added below the
        // main area in the future.
        var openSection = "Comments";
        $(".share-btn").click(function() {
            $("#comments").hide();
            $("#share").show();
            if (!settings.layout["nightModeIsOn"]) {
                  // When the Comment section is closed, override the rule that makes #information's background white so that the unused portion of the page has the same background color as the Comment section.
                $("#information").css("background-color", "rgb(240,240,240)");
            }
            openSection = "Share";
        });
        $(".comment-btn").click(function() {
            if (openSection != "Comments") {
                $("#share").hide();
                // Return back to using a white background for this portion of the page.
                $("#information").css("background-color","")
                $("#comments").show();
                openSection = "Comments";
            }
            else {
                $("#comments textarea").focus();
            }
        });
    };
    
    // 6.2 Make clicking the tag button open and close the Tags section.
    var prepareTagsSection = function(viewportWidth) {
        var viewingTags = false;
        $(".tag-btn").click(function() {
            // If the user is viewing the Tags section, hide it.
            if (viewingTags) {
                $("#tags").css({"display":"none"});
                viewingTags = false;     
            }
            // If the Tags section isn't visible, show it.
            else {
                $("#tags").css({"display":"block"});
                viewingTags = true;
            }
        });
    };
    
    // 6.3 Prepare the behavior of the Like button. Clicking the button toggles between an empty heart and a full heart and increments the like count or decrements it back.
    var prepareLikeButton = function() {
        $(".like-btn").submitOwnDataOnClickThen(function() {
            $(".like-btn .glyphicon").toggleClass("glyphicon-heart glyphicon-heart-empty");
            // To obtain the number of likes, first obtain the text on the Like button, excluding the single space at the beginning.
            var likesLabel = $(".likes-label").text();
            var spacePosition = likesLabel.indexOf(" ");
            var likeCount = parseInt(likesLabel.substring(0,spacePosition));
            // If the icon has been toggled to a full heart, increment the like count. Otherwise it has been toggled to an empty heart, so decrement the like count.
            if ($(".like-btn .glyphicon").hasClass("glyphicon-heart")) {
                likeCount+=1;
            }
            else {
                likeCount-=1;
            }
            // Save the like count to the button text.
            if (likeCount == 1) {
                var likesLabel = likeCount.toString() + " like";
            }
            else {
                var likesLabel = likeCount.toString() + " likes";
            }
            $(".likes-label").text(likesLabel);
        });
    };
    
    // 6.4 Make tapping a text field in the Share section put the link onto the user's clipboard. This helpful mainly for mobile devices.
    var prepareLinkCopying = function() {
        // If the user agent is Safari and the version is less than 10, hide the copy instructions because copying won't work. Safari is specifically targeted, rather than detecting support for the copying
        // feature in general (execCommand), because Safari will falsely return that it supports it when it doesn't, and Chrome will falsely return that it does not support it, even though it does.
        // Chrome user agents contain the word Safari, but out of the major browsers, I only know Safari to contain both the strings "Safari" and "Version/". At a later time, this can be improved by showing
        // the message "Tap a link to copy" instead for users with older Safari browsers and who are also on touch screens. It will require shortening fields to leave room in the browser width.
        var safariVersion = browserInvestigator.detectSafariVersion();
        if (safariVersion && safariVersion < 10) {
            $("#share p.text-center").hide();
        }
        $(".copy-and-paste-set input").on("click",function() {
            // This line of code was included because it improves support for the setSelectionRange function on some versions of Safari, but otherwise it has no effect.
            $("input",this.parentNode).focus();
            // Highlight the contents of the field to the left, in order to copy it to the clipboard. No exception occurs if the upper bound is too high, so instead of retrieving the string to get its length,
            // use a high value to retrieve the contents of the text field.
            $("input",this.parentNode)[0].setSelectionRange(0,99999);
            document.execCommand('copy');
            // Clear the selection. In Chrome, blur() does this, but in IE11, it doesn't.
            $("input",this.parentNode)[0].setSelectionRange(0,0);
            // Cause the text field to lose focus. This gets rid of the blinking cursor. In Chrome, it also gets rid of the outline, letting Chrome users know the text has been copied
            // and they don't have to do anything else.
            $("input",this.parentNode)[0].blur();
            // Change the text of the message for 5 seconds to let users know the text has been copied.
            var originalText = $("#share p.text-center").text();
            $("#share p.text-center").text("Copied!");
            var Timer = setTimeout(function() {
                $("#share p.text-center").text(originalText);
            }, 5000);
        });
    };
    
    // 6. Make the buttons do things.
    var prepareButtons = function(viewportWidth) {
        prepareMainSections(viewportWidth);
        prepareTagsSection(viewportWidth);
        prepareLikeButton();
        prepareLinkCopying();
    };
    
    // 7. This is a CSS layout function. On landscape smartphones and tablets, the pet profile will be presented using two columns with 20px of space between. All other viewports use one column.
    // To do that, however, there needed to be a fixed height specified. Using % units did nothing. I implemented this entirely in the JavaScript file, so the page will still look all right when JavaScript is disabled.
    var setUpTwoColumnRecordDisplay = function() {
        // Reset the layout back to a single column format. Whenever the height of the viewport changes, the height of the pet profile section needs to be recalculated. This happens when switching between
        // landscape and portrait, when opening the keyboard, or when switching to a different device in devtools.
        $("#pet-profile").css({"display":"", "flex-direction":"", "flex-wrap":"", "height":"", "width":""});
        $("#pet-profile > *").css({"margin-left":"", "margin-right":"", "width":""});
        
        var viewportWidth = $(window).width();
        if ((viewportWidth >= 544) && (viewportWidth < 1200)) {
            petProfileHeight = $("#pet-profile").height() / 2;
            $("#pet-profile").css({
                "display": "flex",
                "flex-direction":"column",
                "flex-wrap":"wrap",
                "height": petProfileHeight,
                // Prevent the layout from colliding with the date.
                "width":"100%"
            });
            $("#pet-profile > *").css({
               "margin-left":"10px",
               "margin-right":"10px",
               "width":"calc(50% - 20px)"
            });
        }
        // Because the column width is narrower, text will wrap to the next line earlier. Switching to the two column layout, the profile is likely to have more than half of its prior height.
        // Keep incrementing the height available for the profile its contents can fit in the viewport, instead of wrapping to a third column that overflows the viewport.
        while ($("#pet-profile")[0].scrollWidth > $("#pet-profile").width()) {
            petProfileHeight += 1;
            $("#pet-profile").css("height",petProfileHeight);
        }
    };
    
    // 8. Adjust the layout for browsers browsers not supporting flexboxes, which includes IE9 and IE10. IE11 says it supports flexboxes, but it has a problem here due to a very specific bug related to flex columns,
    // so the function also detects it specifically. When there aren't any comments on the page, so #posted-comments with its top border isn't in the HTML, there isn't any border underneath the Submit button with all
    // of the white area below the textarea. At the same time, having a border at the bottom of the viewport doesn't look right to me. So, I decided to have a fix that adds the bottom border when there aren't any
    // comments yet.
    var fixCommentTextareaForBrowsersNotSupportingFlexboxes = function() {
        var IEVersion = browserInvestigator.detectIEVersion();
        if ((!Modernizr.flexbox || IEVersion == 11) && !settings.layout["nightModeIsOn"]) {
            $("#comments:not(:has(#posted-comments)) #reply-footer").css({"border-bottom": "1px solid rgb(180,180,180)"});
        }
    }
    
    // 9. Set the keyboard controls for the slide page.
    var setKeyboardControls = function() {
        $(window).keydown(function(e) {
            // This condition prevents keyboard control events from happening when a text field or textarea has focus, so that it doesn't interrupt the user's typing.
            if ($(e.target).closest('input[type="text"], textarea').length == 0) {
                // Do not use keyboard controls if the user is pressing the Ctrl or Alt key, because this would interrupt features like copying and pasting comments.
                if (!e.ctrlKey && !e.altKey) {
                    if (e.which == 37) {
                        // If the user presses the left arrow key, visit the previous item in the results list.
                        navigateBack();
                    }
                    else if (e.which == 39) {
                        // If the user presses the left arrow key, visit the next item in the results list.
                        navigateForward();
                    }
                    else {
                            // If the user presses any other key, then move the text cursor to comment textarea field. If the pressed key was for a character, it will immediately appear in the textarea.
                            // This statement will have no effect when the Share section is open instead of the Comment section.
                            $("#comments textarea").focus();
                    }
                }
            }
        });
    };
    
    // Main routine.
    var viewportWidth = $(window).width();
    var viewportHeight = $(window).height();
    // When night mode is enabled, the browser will change the color of the X button when the user zooms in.
    // It will also change the background color of the page when switching between subsections.
    if (viewportWidth < 1200) {
        // Prepare the mobile-only features.
        if ($("#pet-profile")[0]) {
            setUpTwoColumnRecordDisplay();
            $(window).on("throttledresize", setUpTwoColumnRecordDisplay);
        }
        // Determine whether the page is for a panorama, so that this can be taken into account while determining the swiping areas on pageload and while zooming.
        var hasImage = $("#slide-overflow-mobile img")[0];
        if (hasImage) {
            if (viewportWidth / viewportHeight > 1) {
                var viewportAspectRatio = viewportWidth / viewportHeight;
            }
            else {
                var viewportAspectRatio = viewportHeight / viewportWidth;
            }
            var imageWidth = $("#slide-overflow-mobile > img").width();
            var imageHeight = $("#slide-overflow-mobile > img").height();
            var imageAspectRatio = imageWidth / imageHeight;
            if (imageAspectRatio > viewportAspectRatio) {
                // The image is classified as a panorama if its aspect ratio is greater than that of the device in landscape mode.
                // If the image is a panorama, in landscape mode the user can scroll left or right in the x-overflow.
                var isPanorama = true;
            }
            else {
                var isPanorama = false;
            }
        }
        else {
            var isPanorama = false;
            // If the mobile page has a video, and the video has an aspect ratio such that it'd otherwise show only part of the heading below it, add black bars.
            if ($("#slide-overflow-mobile video")[0]) {
                prepareVideo(viewportWidth,viewportHeight);
            }
        }
        pageLoadSwipingAreas();
        if (hasImage) {
            prepareImageZoom();
        }        
    }
    else {
        // Obtain information about the slide from the DOM. The script will pass these variables as arguments to functions which determine whether and how to shrink or enlarge the slide.
        // Find the natural dimensions of the slide (in CSS pixels) and determine whether it is an image or video.
        if ($("#slide-container > img")[0]) {
            // Wait until the image is loaded so its dimensions can be accessed.
            $("#slide-container > img").loadImage(function() {
                var slideWidth = this.naturalWidth;
                var slideHeight = this.naturalHeight;
                // Process the slide arguments and alter the slide's dimensions as needed.
                optimizeDesktopSlide(slideWidth, slideHeight, "#slide-container > img");
                fullMode(slideWidth, slideHeight, "#slide-container > img");
            });
        }
        else {
            // Wait until the video is loaded so its dimensions can be accessed.
            $("#slide-container > video").on("loadedmetadata", function() {
                var slideWidth = $("#slide-container > video")[0].videoWidth;
                var slideHeight = $("#slide-container > video")[0].videoHeight;
                // Process the slide arguments and alter the slide's dimensions as needed.
                optimizeDesktopSlide(slideWidth, slideHeight, "#slide-container > video");
            });
        }
        setKeyboardControls();
    }
    fixCommentTextareaForBrowsersNotSupportingFlexboxes();
    prepareButtons(viewportWidth);
});