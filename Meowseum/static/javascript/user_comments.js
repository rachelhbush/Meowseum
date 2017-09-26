/* Associated files: user_comments.css, user_comments_night.css, user_comments.html, user_comments.js */

$(document).ready(function() {
    /* 1.1 If the user comment's height is less than the slide height, then vertically center it within the height of the slide.
        This couldn't be done with CSS alone without removing the ability of the comment to wrap underneath the slide. */
    var verticallyCenterComments = function() {
        // If the viewport is under 1000px wide and Enlarge is checked, comments appear underneath the slide, so centering isn't needed.
        // If the viewport is over 1000px wide and Enlarge is checked, the only change is that slides increase in size. Comments will still appear to the right of the image, so centering is still needed.
        var viewportWidth = $(window).width();
        if (viewportWidth < 1000) {
            var selector = ".user-comment:not(.enlarged)";
        }
        else {
            var selector = ".user-comment:not(.enlarged), .user-comment.enlarged";
        }
        $(selector).each(function() {
            var that = this;
            $("img, video",this).loadMedia(function() {
                var slideHeight = $("img, video",that).height();
                var commentHeight = $(".comment-text",that).height();
                if (commentHeight < slideHeight) {
                    var margin = (slideHeight - commentHeight) / 2;
                    $(".comment-text",that).css({"margin-top": margin, "margin-bottom": margin});
                    // Sometimes the height of the comment changes after moving it downward, because the first line no longer has to wrap around the comment time.
                    // Check the comment height and center it again, in case it changed.
                    var slideHeight = $("img, video",that).height();
                    var commentHeight = $(".comment-text",that).height();
                    var margin = (slideHeight - commentHeight) / 2;
                    $(".comment-text",that).css({"margin-top":margin,"margin-bottom":margin});
                }
            });
        });
    };
   
    /* 1. When the page loads, add style effects that can only be implemented with JavaScript. */
    var enhanceLayout = function() {
        // Wait until all images are loaded in order to be able to obtain their dimensions.
        // Hide the content while the layout is being reconfigured, because this is better than seeing the text move around.
        $("#user-comments").hide();
        verticallyCenterComments();
        $("#user-comments").show();
        $(window).orientationchange(function() {
            // This statement takes care of a scenario where the Enlarge button is checked and the viewport width falls below 1000px when the device switches orientations.
            // Then the the JavaScript-set properties for centering the CSS will no longer be needed. Remove them before checking if they are still needed.
            $(".user-comment .comment-text").css({"margin-top": "", "margin-top": ""});
            // If needed, recenter the comment again when the user reorients the device, because the height of the comment will change.
            verticallyCenterComments();
        });
    };
    
    /* 2. When the user clicks the Enlarge button, toggle the .enlarged class. Below 1000px, this places the comment underneath a full-width image, and above 1000px the only change is image enlargement. */
    var prepareEnlargeButton = function() {
        $('input[type="checkbox"][name="enlarged-images"]').change(function() {
            $(".user-comment").each(function() {
                if ($(this).hasClass("enlarged")) {
                    // Return comments to being to the right of the vertical center of images.
                    $(this).removeClass("enlarged");
                    verticallyCenterComments();
                }
                else {
                    $(this).addClass("enlarged");
                    var viewportWidth = $(window).width();
                    if (viewportWidth < 1000) {
                        // Remove properties set by JavaScript. At this viewport width, they are not necessary when using the .enlarged class.
                        $(".comment-text",this).css({"margin-top": "", "margin-bottom": ""});
                    }
                    else {
                        verticallyCenterComments();
                    }
                }
            });
        });
    };
    
    /* 0. Main function */
    var main = function() {
        enhanceLayout();
        prepareEnlargeButton();
    };
    main();
});
