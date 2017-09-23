/* File names: header_desktop_v0_1_3.html, header_desktop_v0_1_5.js, header_desktop_v0_1_3.css, header_desktop_night_v0_1_2.css, modals_desktop_v0_1_4.html
   Version date:    Author: Rachel Bush
   Version description:  */

$(document).ready(function () {
    // 1. This function sets up the buttons in the Layout modal which change the playing behavior of GIFs wrapped in .gif-container. */
    var prepareGIFContainerBehaviorButtons = function() {
        // When the page loads, if the user previously chose to autoplay all GIFs, apply the changes to the layout menu again.
        if (settings.layout["playAllDesktopGIFs"]) {
            $("#toggle-autoplay")[0].parentNode.childNodes[0].nodeValue = "Pause all GIFs";
            $("#toggle-autoplay").removeClass("glyphicon-play").addClass("glyphicon-pause");
            $("#gif-mouseout-behavior").hide();
        }
        
        $("#toggle-autoplay").click(function() {
            if (settings.layout["playAllDesktopGIFs"]) {
                // If the user clicked the toggle-autoplay button while autoplay was enabled, pause all the GIFs and enable mouseover behavior.
                settings.desktopPauseAll();
                this.parentNode.childNodes[0].nodeValue = "Play all GIFs";
                $(this.parentNode.childNodes[1]).removeClass("glyphicon-pause").addClass("glyphicon-play");
                // Show the buttons for GIF mouseout behavior again. To be able to show or hide the instructions,
                // the instructions and the buttons were wrapped with <div id="gif-mouseout-behavior">.
                $("#gif-mouseout-behavior").show();
                settings.layout["playAllDesktopGIFs"] = false;
            }
            else {
                // If the user clicked the toggle-autoplay button while autoplay was disabled or all GIFs were paused, play all the GIFs.
                settings.desktopPlayAll();
                this.parentNode.childNodes[0].nodeValue = "Pause all GIFs";
                $(this.parentNode.childNodes[1]).removeClass("glyphicon-play").addClass("glyphicon-pause");
                // Hide the buttons for GIF mouseout behavior.
                $("#gif-mouseout-behavior").hide();
                settings.layout["playAllDesktopGIFs"] = true;
            }
            settings.update();
        });
    
        // When the page loads, make the button reflecting current GIF mouseout behavior appear pressed.
        // Even if this section is hidden because all GIFs are currently playing, the user will see it when he or she presses the pause button.
        if (settings.layout["reactionToGIFMouseleave"] == "finish") {
            $("#finish-option").addClass("active");
        }
        else if (settings.layout["reactionToGIFMouseleave"] == "pause") {
            $("#pause-option").addClass("active");
        }
        else {
            $("#stop-option").addClass("active");
        }
        // When the user clicks any of the buttons for mouseout behavior, if the button wasn't already active (stuck in a pressed down state), the previously active button becomes
        // unpressed. The clicked button will stay pressed until the user clicks another of the three buttons.
        $("#finish-option").click(function() {
            if (settings.layout["reactionToGIFMouseleave"] != "finish") {
                $("video").off("mouseover").off("mouseout");
                settings.finishLoopOnMouseout();
                $("#finish-option").addClass("active");
                $("#pause-option").removeClass("active");
                $("#stop-option").removeClass("active");
                settings.layout["reactionToGIFMouseleave"] = "finish";
                settings.update();
            }
        });
        $("#pause-option").click(function() {
            if (settings.layout["reactionToGIFMouseleave"] != "pause") {
                $("video").off("mouseover").off("mouseout");
                settings.pauseVideoOnMouseout();
                $("#finish-option").removeClass("active");
                $("#pause-option").addClass("active");
                $("#stop-option").removeClass("active");
                settings.layout["reactionToGIFMouseleave"] = "pause";
                settings.update();
            }
    
        });
        $("#stop-option").click(function() {
            if (settings.layout["reactionToGIFMouseleave"] != "stop") {
                $("video").off("mouseover").off("mouseout");
                settings.stopVideoOnMouseout();
                $("#finish-option").removeClass("active");
                $("#pause-option").removeClass("active");
                $("#stop-option").addClass("active");
                settings.layout["reactionToGIFMouseleave"] = "stop";
                settings.update();
            }
        });
    };
    
    // 0. Main function.
    var main = function() {
        prepareGIFContainerBehaviorButtons();
    };
    main();
});