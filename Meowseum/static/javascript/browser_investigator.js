/* Description: This file contains a namespace for the sitewide JavaScript related to detecting information about the user agent.
   This is very helpful in situations where the bug is specific to a popular browser, and it isn't possible to detect support for a feature instead.
   Currently, this file is only used for detecting IE versions, Safari versions, and autoplay support.
*/

// Don't wait until the DOM is loaded because this file doesn't manipulate the DOM, and it doesn't even use jQuery.
// Create the namespace for all the functions.
window.browserInvestigator = window.browserInvestigator || {};

// This Boolean function detects if a certain CSS property is supported by the browser.
browserInvestigator.isPropertySupported = function(property) {
    // Detect if the property exists on a DOM element that is guaranteed to be there by the time the page is loaded. This script is in <head>, so <head> will always be there.
    return property in document.head.style;
}

// This function detects if the user agent is Internet Explorer. If IE, it returns the version as an integer. Otherwise, it returns false.
// After storing the returned value, you can write conditions of the form "IEVersion && IEVersion < 10".
// Currently, I use this because only IE has problems with the image load event, and only IE11 has problems with custom file browse buttons.
browserInvestigator.detectIEVersion = function() {
   // From IE's first version until IE10, its user agent had the "MSIE" token.
   var IEresult1 = navigator.userAgent.search("MSIE");
   // Since IE11, Internet Explorer comes with the "rv:" token.
   var IEresult2 = navigator.userAgent.search("rv:");
   // IE9 introduced the "Trident" token. This will be used to distinguish IE from Firefox, which also uses "rv:" in its user agent.
   var IEresult3 = navigator.userAgent.search("Trident");
   // Return the version if IE10 or lower.
   if (IEresult1 != -1) {
       // Retrieve the slice of the user agent extending from "MSIE" to the end of the user agent.
       var slicedAgent = navigator.userAgent.slice(IEresult1,navigator.userAgent.length);
       // Retrieve the position of the first space and first semicolon within the sliced user agent, as in " MSIE 9.0;", because they will serve as the delimiters of the version number.
       var firstSpacePosition = slicedAgent.search(" ");
       var firstSemicolonPosition = slicedAgent.search(";");
       // Retrieve the version, as in "9.0", and round down while converting to a integer.
       var IEversion = parseInt( slicedAgent.slice(firstSpacePosition + 1,firstSemicolonPosition));
       return IEversion;
   }
   // Return the version if IE11 or higher.
   else if (IEresult2 != -1 && IEresult3 != -1) {
       // Retrieve the slice of the user agent extending from "rv:" to the end of the user agent.
       var slicedAgent = navigator.userAgent.slice(IEresult2,navigator.userAgent.length);
       // Retrieve the position of the first colon and first parenthesis within the sliced user agent, as in ":11.0)", because they will serve as the delimiters of the version number.
       var firstColonPosition = slicedAgent.search(":");
       var firstSemicolonPosition = slicedAgent.search(";");
       var IEversion = parseInt( slicedAgent.slice(firstColonPosition + 1,firstSemicolonPosition));
       return IEversion;
   }
   else {
       return false;
   }
};

// This function detects if the user agent is Safari. If the browser isn't Safari, the function returns false.
// After storing the returned value, you can write conditions of the form "SafariVersion && SafariVersion < 10"
// The function was written because the JavaScript's built-in methods for copying, cutting, and pasting are only supported in Safari 10+, with no way to do feature detection. 

// If Safari, the function returns the version as a float to one decimal place. The first-decimal version number hasn't been used yet, but many features
// like jQuery version compatibility and webkit vendor prefix guides refrence the first-decimal version number. If the browser is Safari but the version is unknown, the function returns -1.
// For example, the browser may return "Mobile Safari 1.1.3", and most sources indicating what features are supported by Safari are not referring to Mobile Safari.

// This isn't 100% accurate, because there are a few Safari user agents not containing Safari, but those user agents have been described by
// useragentstring.com as no longer having any meaning, or they are lying about the identity of the browser.
browserInvestigator.detectSafariVersion = function() {
    // Retrieve the user agent. Changing this statement will allow the function to be tested in the console of a browser other than Safari.
    var userAgent = navigator.userAgent;
    var safariResult1 = userAgent.search("Safari");
    // Filter out browsers that are Chrome or a related project like Chromium.
    // The Chrome browser's user agent contains the string "Safari", even though it supports features Safari doesn't.
    if ((safariResult1 != -1) && (userAgent.search("Chrome") == -1)) {
        var safariResult2 = userAgent.search("Version/");
        var safariResult3 = userAgent.search("AppleWebKit/");
        // If the user agent contains "Version/", then the version number will be located after it in nearly all releases after 3.0.
        if (safariResult2 != -1) {
            // Retrieve the slice of the user agent extending from "Version/" to the end of the user agent.
            var slicedAgent = userAgent.slice(safariResult2,userAgent.length);
            // Retrieve the position of the first forward slash and first space in the sliced user agent, which will be used as the delimiters of the version number.
            var firstForwardSlashPosition = slicedAgent.search("/");
            var firstSpacePosition = slicedAgent.search(" ");
            // Retrieve a version string of the form "7.0.3" or "5.0".
            var fullSafariVersion = slicedAgent.slice(firstForwardSlashPosition + 1,firstSpacePosition);
            // Split the version string into an array of each number separated by a "."
            var SafariVersionArray = fullSafariVersion.split();
            if (SafariVersionArray.length >= 2) {
                // Create a new array from only the first two elements and join them to get the version number string.
                var SafariVersion = SafarVersionArray.slice(0,2).join();
            }
            else {
                // The array contains only the major version, so take it out of the array.
                var SafariVersion = SafariVersionArray[0];
            }
            // Convert to a float with one decimal place, such as "5.1".
            SafariVersion = parseFloat(SafariVersion);
            return SafariVersion;
        }
        // Below Safari 3.0, the user agent doesn't contain "Version/", but it can be indirectly determined from the part of the user agent for the WebKit engine number.
        // For example, "AppleWebKit/125.1" with the number in the 100's is only associated with Safari 1.2.
        // This doesn't work well for versions over 3.0, because in that range the WebKit version can actually decrease between greater Safari versions.
        else if (safariResult3 != -1) {
            // Retrieve the slice of the user agent extending from "AppleWebKit/" to the end of the user agent.
            var slicedAgent = userAgent.slice(safariResult3,userAgent.length);
            // Retrieve the position of the first forward slash and first space in the sliced user agent, which will be used as the delimiters of the version number.
            var firstForwardSlashPosition = slicedAgent.search("/");
            var firstSpacePosition = slicedAgent.search(" ");
            // Retrieve a version string of the form "531.22.7" or "533.16" or "531.2+".
            var fullWebKitVersion = slicedAgent.slice(firstForwardSlashPosition + 1,firstSpacePosition);
            // Trim any "+" off the end.
            fullWebKitVersion = fullWebKitVersion.trim("+");
            // Split the version string into an array of each number separated by a "."
            var WebKitVersionArray = fullWebKitVersion.split();
            // Obtain the integer before the first "." in the WebKit version.
            var majorWebKitVersion = parseInt(WebKitVersionArray[0]);
            if (majorWebKitVersion >= 537) {
                // The oldest the Safari version can be is 7.0. 
                return 7.0;
            }
            else if (majorWebKitVersion >= 533) {
                // The oldest the Safari version can be is 5.0. 
                return 5.0;
            }
            else if (majorWebKitVersion >= 525) {
                // The oldest the Safari version can be is 3.1. Using the WebKit version is only accurate for 3.0 or lower.
                return 3.1;
            }
            else if (majorWebKitVersion >= 500) {
                return 3.0;
            }
            else if (majorWebKitVersion >= 400) {
                return 2.0;
            }
            else if (majorWebKitVersion >= 200) {
                return 1.3;
            }
            else if (majorWebKitVersion >= 100) {
                return 1.2;
            }
            else {
                return 1.0;
            }
        }
        // If the browser is Safari, but the version is unknown, return -1.
        else {
            return -1;
        }
    }
    else {
        return false;
    }
};

/*
$(document).ready(function() {
    // 0. Detect whether the browser, in combination with the device's operating system, permits videos to be played without user interaction. This includes the autoplay attribute
    // and autoplay JavaScript. This function was added because Modernizr is currently unable to reliably feature-detect autoplay.
    // The iOS only allows autoplay for videos with the muted attribute in order to support only GIFs, so the global constant browserInvestigator.AUTOPLAYSUPPORT is a dictionary
    // with two keys with Boolean values, "canAutoplayAllVideos" and "canAutoplayMutedVideos".
    var detectAutoplaySupport = function() {
        if (localStorage.autoplaySupport) {
            // Autoplay support has already been detected on a previous page.
            browserInvestigator.AUTOPLAYSUPPORT = JSON.parse(localStorage.autoplaySupport);
        }
        else {
            browserInvestigator.AUTOPLAYSUPPORT = {
                "canAutoplayAllVideos": true,
                "canAutoplayMutedVideos": true
            };
            // Store the result into local storage.
            localStorage.autoplaySupport = JSON.stringify(browserInvestigator.autoplaySupport);
        }
    };
    
    detectAutoplaySupport();
});
*/