/* File names: gallery_main_v0_1_9.html, gallery_v0_1_9.js, gallery_v0_1_6.css, gallery_night_v0_1_0.css  Version date:  Author: Rachel Bush
   Version description: 
   Known issues: The columns variable is a jQuery set, so by convention I should have written the name starting with a $.
*/

$(document).ready(function() {
    // 2.3 After the previous slide transfer has been found to decrease the evenness of the gallery's columns, move the slide back to its original location:
    // Input: The original index of the slide, the <li> containing the slide (jQuery element), and the <ul> DOM element.
    // Output: None.
    var moveSlideBack = function(i, $shortestListItem, fromColumn) {
        var $fromColumnListItems = $("li",fromColumn);
        $shortestListItem.remove();
        if ($fromColumnListItems.length > 0) {
            if (i > 0) {
                $shortestListItem.insertAfter($fromColumnListItems[i-1]);
            }
            else {
                $shortestListItem.insertBefore($fromColumnListItems[0]);
            }
        }
        else {
            $shortestListItem.prependTo(fromColumn);
        }
    };
    
    // 2.2 Transfer the shortest slide (here referring to a <li> element) in one column to another column. A prior version of this function moved the last slide in the column, which meant that when the program
    // stopped because it detected a negative change, there was still a more optimal configuration involving moving a shorter slide instead. Using the shortest slide ensures the height difference between columns
    // can only shrink during each transfer, not grow.
    
    // If it is possible, the slide will be inserted within the same row, at the same index within the destination column, in order to be as close to the original sorting order as possible.
    // If keeping it in the same row isn't possible, then the list item will be the destination column's last child element.
    // Input: columns, a jQuery set of <ul>s. fromColumn, an integer for the position of the column from which to move an slide. toColumn, an integer for the position of the column to which to move the slide.
    // Output: The index of the slide which was transferred.
    var transferSlideBetweenColumns = function(columns, fromColumn, toColumn) {
        // Find the shortest slide in the from column.
        var $fromColumnListItems = $("li",columns[fromColumn]);
        var fromColumnHeights = [];
        fromColumnHeights[0] = $($fromColumnListItems[0]).outerHeight();
        var shortestListItemIndex = 0;
        for (var i = 1; i < $fromColumnListItems.length; i++) {
            fromColumnHeights[i] = $($fromColumnListItems[i]).outerHeight();
            if (fromColumnHeights[i] < fromColumnHeights[i-1]) {
                shortestListItemIndex = i;
            }
        }
        var $shortestListItem = $($fromColumnListItems[shortestListItemIndex]);
        $shortestListItem.remove();
        var $toColumnListItems = $("li",columns[toColumn]).length;
        if (shortestListItemIndex+1 <= $toColumnListItems.length) {
            $shortestListItem.insertBefore(columns[toColumn][shortestListItemIndex]);
        }
        else {
            $shortestListItem.appendTo(columns[toColumn]);
        }
        // Keep track of the columns used for the transfer in case the slide being moved results in a negative change and the slide needs to be moved back.
        return [shortestListItemIndex, $shortestListItem, columns[fromColumn]];
    };

    // 2.1.1 Determine the greatest difference within an array. Input: An array.
    // Output: An array containing [greatestDifference, positionOfSmallestValue, positionOfLargestValue].
    var findGreatestDifferenceWithinAnArray = function(array) {
        var greatestDifference = 0;
        var positionOfSmallestValue = 0;
        var positionOfLargestValue = 1;
        for (var i = 0; i < array.length; i++) {
            for (var j = 0; j < array.length; j++) {
                if (i != j) {
                    var difference = Math.abs(array[i] - array[j]);
                    if (difference > greatestDifference) {
                        greatestDifference = difference;
                        if (array[i] > array[j]) {
                            positionOfLargestValue = i;
                            positionOfSmallestValue = j;
                        }
                        else {
                            positionOfLargestValue = j;
                            positionOfSmallestValue = i;
                        }
                    }
                }
            }
        }
        return [greatestDifference, positionOfSmallestValue, positionOfLargestValue];
    };

    // 2.1 Determine the greatest difference between heights of columns of slides.
    // Input: columns, a jQuery set of <ul>s.
    // Output: An array containing [greatestDifference, positionOfSmallestValue, positionOfLargestValue].
    var findGreatestHeightDifferenceBetweenColumns = function(columns) {
        // Get the height of each column.
        var columnHeightArray = [];
        for (var i = 0; i < columns.length; i++) {
            columnHeightArray[i] = $(columns[i]).outerHeight();
        }
        return findGreatestDifferenceWithinAnArray(columnHeightArray);
    };

    // 2. After the slides are arranged into the appropriate amount of columns, move slides from the longest column to the shortest column in order to reduce the height of the oveall
    // layout and make the heights of each column more even.
    // Input: None. Output: None.
    var evenOutSlideColumnHeights = function() {
        var columns = $("#gallery .container-fluid ul");
        // If all columns have 1 slide or less, then the program doesn't need to do anything. Determine whether at least one column has multiple slides.
        var aColumnHasMultipleSlides = false;
        for (var i = 0; i < columns.length; i++) {
            if ($(columns[i]).children().length > 1) {
                aColumnHasMultipleSlides = true;
            }
        }
        if (aColumnHasMultipleSlides) {
            // Move a slide from the longest column to the shortest column until the greatest height difference is minimized.
            // First, initialize by storing variables related to the greatest difference between the height of the slide columns before and after moving an slide.
            var returnValueArray = findGreatestHeightDifferenceBetweenColumns(columns);
            var oldGreatestHeightDifference = returnValueArray[0], shortestColumn = returnValueArray[1], longestColumn = returnValueArray[2];
            if (oldGreatestHeightDifference > 0) {
                var previouslyMovedSlideInformation = transferSlideBetweenColumns(columns, longestColumn, shortestColumn);
            }
            returnValueArray = findGreatestHeightDifferenceBetweenColumns(columns);
            var newGreatestHeightDifference = returnValueArray[0], shortestColumn = returnValueArray[1], longestColumn = returnValueArray[2];
            var improvement = oldGreatestHeightDifference - newGreatestHeightDifference;
            // Begin moving more slides until there isn't any improvement in the layout.
            while (improvement > 0 && newGreatestHeightDifference > 0) {
                var previouslyMovedSlideInformation = transferSlideBetweenColumns(columns, longestColumn, shortestColumn);
                oldGreatestHeightDifference = newGreatestHeightDifference;
                returnValueArray = findGreatestHeightDifferenceBetweenColumns(columns);
                newGreatestHeightDifference = returnValueArray[0], shortestColumn = returnValueArray[1], longestColumn = returnValueArray[2];
                improvement = oldGreatestHeightDifference - newGreatestHeightDifference;
            };
            // If the last move led to a negative change, then move the slide back. This has to be the slide that was previously moved, in case the slide that was previously moved was the only one in its column.
            if (improvement < 0) {
                moveSlideBack(previouslyMovedSlideInformation[0], previouslyMovedSlideInformation[1], previouslyMovedSlideInformation[2]);
            }
        }
    };
    
    // 1.1 Calculate the number of columns needed for the current viewport width. Input: None.
    // Output: An array containing [numberOfColumns, columnString], where columnString is the appropriate Bootstrap class for dividing the viewport into the number of columns.
    var getNumberOfColumns = function() {
        // Initially, there are three columns of slides. This will make the page look less broken when JavaScript is disabled, because three columns looks the best across all common
        // viewport widths. First, determine the number of columns that should be used. Bootstrap 4 uses 544px as the breakpoint for phones in landscape mode, and 1200px is their
        // cutoff for laptops. CSS viewport width includes the scrollbar and JavaScript viewport width excludes it, but there isn't a way to tell whether one is there.
        // So, the mobile header is replaced by the laptop/desktop header at 1200px, and the layout goes to four columns at 1217px.
        var viewportWidth = $(window).width();
        if (viewportWidth < 544) {
            var numberOfColumns = 2;
            var columnString = "col-xs-6";
        }
        else if (viewportWidth >= 544 && viewportWidth < 1200) {
            var numberOfColumns = 3;
            var columnString = "col-xs-4";
        }
        else {
            var numberOfColumns = 4;
            var columnString = "col-xs-3";
        }
        return [numberOfColumns, columnString];
    };
    
    // 1. Depending on the viewport width, the layout has a certain number of slides per row. The slides will be of the same width, which produces a pattern like a hardwood floor.
    //    A smartphone in portrait mode will see two columns of slides, a tablet will see three columns of slides, and a laptop will see four columns of slides.
    //    This will be implemented by sorting the slides into two, three, or four <ul>s, each wrapped in a Bootstrap column wide enough for a half, third, or fourth of the page.
    var rearrangeSlidesIntoColumns = function() {
        var returnValueArray = getNumberOfColumns();
        var numberOfColumns = returnValueArray[0], columnString = returnValueArray[1];
        
        // Remove the <ul>s and Bootstrap columns, but leave the list items.
        // The selectors in this function are carefully written so that, on user's gallery pages for uploads and likes, there can be a <nav> above the main .container.
        $("#gallery .container-fluid li").unwrap().unwrap();
        // Obtain the jQuery set of list items for each slide, and use it to determine how the grid of slides should look.
        var $slides = $("#gallery .row > li");
        var numberOfSlides = $slides.length;
        var slidesPerColumn = Math.floor(numberOfSlides / numberOfColumns);
        var numberInLastRow = numberOfSlides % numberOfColumns;
        
        // After determining how the slides will be sorted, the <li>s will be wrapped in a copy of this <ul>.
        var ulNode = $('<ul class="list-unstyled">');
        // Split the jQuery set into an array of jQuery sets representing each column. If there are an unevenly divisible number of slides, the first few columns have an extra one.
        // To do this, the end index on the first few slices will be increased by one for each column with an extra slide, and all subsequent columns will have both the beginning
        // and end index shifted.
        var colArray = [];
        var j=0;
        for (var i=0; i < numberOfColumns; i++) {
            if (j < numberInLastRow) {
        	    colArray[i] = $slides.slice(i * slidesPerColumn + j, (i+1) * slidesPerColumn+j+1);
                j+=1;                    
            }
            else {
        	    colArray[i] = $slides.slice(i * slidesPerColumn + j, (i+1) * slidesPerColumn+j);
            }
            colArray[i].wrapAll(ulNode);
        }
        
        // Wrap each <ul> in a <div> with the appropriate Bootstrap column class.
        var divNode = $("<div>");
        $("#gallery .container-fluid ul").wrap(divNode);
        $("#gallery .row > div").addClass(columnString);
    };

    // 0. Main routine.
    var main = function() {
        rearrangeSlidesIntoColumns();
        $(window).load(function() {
            setTimeout(function() {
                // After all the image and videos are loaded, move them around to make the height of each column more even.
                // The 500ms wait accounts for the time in which the heights of the columns will change as images and videos themselves appear on the page.
                // I concluded this was the cause after testing in which JavaScript still hadn't gotten the height of the column correct after all the media dimensions had loaded. 
                evenOutSlideColumnHeights();
                settings.prepareGIFs();
            }, 500);
        });
        $(window).on("throttledresize",function() {
            rearrangeSlidesIntoColumns();
            evenOutSlideColumnHeights();
            settings.prepareGIFs();
        });
    }
    main();
});