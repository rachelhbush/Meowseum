/* File names: forms_v0_0_0_44.js   Version date: Author: Rachel Bush
   File description: This file contains functions that can be used with all forms. All functions are stored within the "forms" namespace.
   This is library JavaScript, written for sitewide use.
   
   In order to make sure the event handlers will still be attached to elements yet to be injected into the DOM by AJAX,
   the script attaches events to the document object when using event delegation, as in $(document).on("event", "selector", handler). I originally wrote this script while assuming
   static content, so not every function does this. If there any performance issues arise, efficiency may be able to be increased by rewriting the script to attach events to
   the static ancestor element closest to the dynamic content in the hierarchy.
   Version description: 
*/

$(document).ready(function() {
    // This section is for jQuery plug-ins that this script creates and uses, as well as library functions which the main function in this file doesn't execute. 
    
    // 1. Use this method if you want to make sure a checkbox is checked or unchecked, regardless of its prior status.
    // The method tests for whether the checkbox has changed, and if it has, it triggers the "change" event.
    // Input: Boolean
    // Output: None
    $.fn.changeValue = function(newValue) {
        this.each(function() {
            var priorValue = $(this).prop("checked");
            if (priorValue != newValue) {
                $(this).prop("checked",newValue);
                $(this).trigger("change");
            }
        });
        // Allow chaining.
        return this;
    }
    
    // 2. This method, belonging to a default checkbox, allows checking or unchecking it via JavaScript.
    $.fn.check = function() {
        var isChecked = this.prop("checked");
        if (isChecked) {
            // Uncheck the checkbox.
            this.prop("checked",false);
        }
        else {
            // Check the checkbox.
            this.prop("checked",true);
        }
        // Custom checkboxes will update when the inner checkbox has a "change" event, when the user manually checks a checkbox (via mouse or keyboard),
        // but not when the checkbox is checked via script. This is because when the script checks a checkbox via a "change" event handler, it can start running after the custom checkbox updater.
        // So, check again here that the custom checkbox reflects the status of the inner default checkbox.
        var $parent = $(this).parent();
        if ($parent.hasClass("custom-checkbox")) {
            forms.adjustCustomCheckbox.call(this);
        }
        // Make scripted checking compatible with the change event. Without the following statement, the change event only occurs when the user directly clicks a checkbox.
        this.trigger("change");
        // Allow chaining.
        return this;
    };

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    
    // Create a namespace for the sitewide JavaScript form functions.
    window.forms = window.forms || {};
    
    // 1. Bootstrap .glyphicon-search icons that are nested in a <form> will submit the <form> when clicked.
    forms.searchIconsSubmit = function() {
        $("form .glyphicon-search").click(function() {
            $(this).closest("form").submit();
        });
    };
    
    // 2.1. This is the main function for forms.consistentFormTableColumnWidths, invoked when the page loads and when the viewport resizes.
    forms.makeColumnWidthsConsistent = function() {
        var viewportWidth = $(window).width();
        if (viewportWidth > 544) {
            $("form.consistent-columns").each(function() {
                $tables = $("table.form", $(this));
                // Find the width of the widest header column.
                largestWidth = 0;
                for (var i=0; i < $tables.length; i++) {
                	width = $("tbody:first-child > tr:first-child > th:first-child", $tables[i]).width();
                    if (width > largestWidth) {
                        largestWidth = width;
                    }
                }
                console.log(largestWidth);
                for (var i=0; i < $tables.length; i++) {
                    // Make each form table's header column as wide as the widest column.
                    $("th", $tables[i]).width(largestWidth);
                }
            });
        }
        else {
            // Remove any scripting of the width property.
            $("form.consistent-columns th").css("width","");
        }
    };
    
    // 2. This is a CSS-styling function involving selection too complex for a style sheet. It will make form tables within <form class="consistent-columns"> use the same widths for their two columns,
    // by using the width where the header column is widest. The effect only occurs above 544px, the landscape smartphone range, so that below that the fields have more room.
    forms.consistentFormTableColumnWidths = function() {
        forms.makeColumnWidthsConsistent();
        $(window).on("throttledresize", forms.makeColumnWidthsConsistent);
    };
    
    // 3. For non-mobile devices, multiselects require pressing Ctrl in order to select multiple options. This function improves the behavior of a multiselect by making it so that
    // clicking an option will select or unselect it. Many sites recommend more user-friendly alternatives to the multiselect, such as an overflow with checkboxes, but this
    // function will make the form more intuitive until such an alternative is implemented. The function assumes the script is needed only if the screen is over 1200px wide.
    // iOS and Android provide their own interface for the multiselect, styling it like a button which launches a modal.
    //  Known issues:        Clicking an option at the top of the multiselect and then clicking an option at the bottom of the multiselect will scroll the multiselect back to the top.
    //                       The issue is caused by preventDefault(), and I made it so that it at least does not arise when clicking while using the keyboard controls. 
    // Attempted solutions: I do not think that this issue can be fixed. I tried using focus() and blur() after changing the property, and it had no effect. I tried
    //                       preventing the default action for focus() on <option> and on <select>, and it had no effect. jQuery's scrollTop() was able to get the
    //                       scroll position of the multiselect, but it had no effect when I tried to use this value to set the scroll position. Using a timer to
    //                       wait for a fraction of a millisecond before invoking the method for an attempted fix had worked in other situations,
    //                       but this time it had no effect.
    //                       
    //                       In the future, to override default form control behavior, it would probably be easier to hide the form control and create a separate <div> which manipulates
    //                       the hidden form control's properties. For a multiselect, the <div> would be a <ul> containing a list of items in an overflow.
    forms.keyboardlessMultiselects = function() {
        var viewportWidth = screen.width;
        if (viewportWidth > 1200) {
            $multiselects = $("select[multiple]");
            $multiselects.each(function() {
                var numberOfOptions = $("option", this).length;
                // Retrieve a jQuery set of all the <option>s in the multiselect.
                var $options = $("option",this);
                for (var i=0; i < numberOfOptions; i++) {
                    $($options[i]).on('mousedown',(function(i) {
                        // Use a closure so that each <option>'s event handler will remember a different i value.
                        var eventHandler = function(e) {
                            // If the user still prefers to multiselect with the keyboard, make no changes to the default behavior.
                            if (!e.shiftKey && !e.ctrlKey) {
                                e.preventDefault();
                            }
                            // Keep the browser from unselecting all other selected options on mousedown without pressing Ctrl.
                            if (!e.ctrlKey) {
                                var status = $(this).prop("selected");
                                if (status == true) {
                                    $(this).prop("selected", false);
                                }
                                else {
                                    $(this).prop("selected", true);
                                }
                                // Modifying a property of an <option> removes focus from the <select>, resulting in <option>s being highlighted grey. Keep the focus on the <select> so
                                // <option>s stay highlighted blue.
                                $(this).parent().focus();
                            }
                        }
                        return eventHandler;
                    })(i));
                }
            });
        }
    };
    
    // 4.1. This jQuery plug-in method, belonging to .checkbox-dropdown, sets its label to be a string like "1 option selected" or "3 options selected".
    // This will be visible in the rectangle above the options, and it will continue to be visible while the dropdown is closed.
    $.fn.setCheckboxDropdownLabel = function(zeroCheckedLabel) {
        // Count the number of options that are checked, excluding the "any" or "Any" checkbox if there is one.
        var numberOfCheckedOptions = $('input[type="checkbox"]:not([value="any"]):not([value="Any"]):checked',this).toArray().length;
        if (numberOfCheckedOptions == 0) {
            // Reset to the initial label.
            $("label",this).html(zeroCheckedLabel + '<span class="caret"></span>');
        }
        else if (numberOfCheckedOptions == 1) {
            $("label",this).html(numberOfCheckedOptions.toString() + ' option selected<span class="caret"></span>');
        }
        else {
            $("label",this).html(numberOfCheckedOptions.toString() + ' options selected<span class="caret"></span>');
        }
    };
    
    // 4.2. This jQuery plug-in method, belonging to .checkbox-dropdown, makes checkbox dropdowns open upward if it would allow more options to be displayed in the viewport at once.
    //     It makes the dropdown open upward by adding the class .above if it is needed for the dropdown to fit within the viewport.
    //     It also determines what the maximum height of the dropdown option container should be. If there is plenty of room, it leaves the maximum height at enough for 20 options.
    //     If the dropdown is long enough to scroll regardless of which way the dropdown opens, then it adds .above if the dropdown is below the viewport's center.
    //     The conditions in this function were written to echo the behavior I saw for the <select> dropdown in Chrome Developer Tools while simulating mobile devices.
    $.fn.setCheckboxDropdownOpenCSS = function() {
        // First, gather all the variables that will be used in the conditions.
        var viewportHeight = $(window).height();
        var closedDropdownHeight = $("label",this).outerHeight();
        var totalDropdownOptionsHeight = $("label+div",this).outerHeight();
        // Find the Y coordinate of the top of the dropdown container, when closed, relative to the viewport's top-left corner.
        var clientYTopCoordinate = this.offset().top - $(window).scrollTop();
        // Find the Y coordinates for the bottom and vertical center of the dropdown container.
        var clientYBottomCoordinate = clientYTopCoordinate + closedDropdownHeight;
        var clientYCenterCoordinate = clientYTopCoordinate + closedDropdownHeight / 2;
        // Find the space below the dropdown label in the viewport.
        var bottomRoomForDropdown = viewportHeight - clientYBottomCoordinate;
        // Find the space above the dropdown label in the viewport.
        var topRoomForDropdown = clientYTopCoordinate;
        
        // If there is room for the dropdown to drop downward without scrolling, it should drop downward.
        // If this isn't the case, and there is room for the dropdown options without scrolling if it opens upward, then have it open upward.
        // If the dropdown options would scroll either way, then the dropdown opens upward if its center is below the center of the viewport. It opens downward if its center is at or above the center of the viewport.
        if ((bottomRoomForDropdown >= totalDropdownOptionsHeight) || ((bottomRoomForDropdown < totalDropdownOptionsHeight) && (topRoomForDropdown < totalDropdownOptionsHeight) && clientYCenterCoordinate <= viewportHeight / 2)) {
            // The dropdown opens downward.
            this.removeClass("above");
            var roomForDropdown = bottomRoomForDropdown;
        }
        else {
            // The dropdown opens upward.
            this.addClass("above");
            var roomForDropdown = topRoomForDropdown;
        }
        // Last, if the room for the dropdown is less than the room needed for 20 options, restrict the maximum height to the available room.
        if (roomForDropdown < 448) {
            $("label+div",this).css({"max-height":roomForDropdown});
        }
    };
    
    // These two functions are for  user-friendly alternatives to the multiselect, ones which won't require users without a mobile OS (Android or iOS) to hold down Ctrl or Shift.
    // See the CSS comments for more detail.
    // Known issues: 1. The Shift+Click functionality won't be implemented until after the site has been launched. It will be considerably more difficult
    //                  and involve keeping track of how the selected range changes using a follower variable.
    //               2. The feature which disables text selection could be better supported by browsers (IE9, Android 4.1 and older) if JavaScript were used to disable it instead of a CSS rule.
    
    // 4. Checkbox dropdowns render like a <select> dropdown, but with checkboxes. The script requires that each checkbox dropdown uses a unique name for its set of checkboxes.
    forms.checkboxDropdowns = function() {
        $(".checkbox-dropdown").each(function() {
            // Store the checkbox dropdown into a variable, because it will be referenced by multiple event handlers for other elements.
            // (The relative methods can't be used because some of these elements will be higher in the DOM, so if there are multiple checkbox dropdowns, they wouldn't know which is the right one.)
            var $checkboxDropdown = $(this);
            // Store the text used when no checkboxes are checked.
            var zeroCheckedLabel = $("label",this).text();
            // If there are any checkboxes that are checked by default, change the label when the page loads.
            $checkboxDropdown.setCheckboxDropdownLabel(zeroCheckedLabel);
            // Click or touch the dropdown to open and close it.
            $("label",this).mousedown(function() {
                $checkboxDropdown.toggleClass("open");
                $checkboxDropdown.setCheckboxDropdownOpenCSS();
            });
            // Click an option to check a checkbox. If the element directly clicked is the checkbox itself, then do nothing, because the two checks would cancel out.
            $("div > div",this).mousedown(function(e) {
               var $checkbox = $('input[type="checkbox"]', this);
               if (e.target != $checkbox[0]) {
                   $checkbox.check();
               }
           });
           $('input[type="checkbox"]',this).change(function() {
                // Adjust the option highlighting.
                var isChecked = $(this).prop("checked");
                if (isChecked) {
                    $(this).parent().addClass("selected");
                }
                else {
                    $(this).parent().removeClass("selected");
                }
                $checkboxDropdown.setCheckboxDropdownLabel(zeroCheckedLabel);
           });
            // Click or touch anywhere outside the dropdown to close it.
            $(document).mousedown(function(e) {
                // Detect whether the clicked object is the dropdown or has the dropdown as an ancestor. If neither is true, the method returns an empty array, so the script tests the return value's length.
                if ($(e.target).closest($checkboxDropdown).length == 0) {
                    // Reset the direction in which the dropdown opens, and any maximum height restrictions related to fitting it in the viewport.
                    // In case the user has scrolled, these values will be recalculated next time the dropdown opens.
                    $checkboxDropdown.removeClass("open above");
                    $("label+div",$checkboxDropdown).css("max-height","");
                    
                    // If only one item is checked, then when the dropdown closes, replace the label "1 option selected" with the label of the selected option.
                    var numberOfCheckedOptions = $('input[type="checkbox"]:not([value="any"]):not([value="Any"]):checked',$checkboxDropdown).toArray().length;
                    if (numberOfCheckedOptions == 1) {
                        $("label",$checkboxDropdown).html($('input[type="checkbox"]:not([value="any"]):not([value="Any"]):checked',$checkboxDropdown).parent().text() + ' <span class="caret"></span>');
                    }
                }
            });
            // If the dropdown has a "Clear" button because it has a lot of options, then make it uncheck all the options when clicked.
            $('.btn-primary',this).click(function() {
                var checkboxGroupName = $('input[type="checkbox"]',$checkboxDropdown).prop("name");
                $('input[type="checkbox"][name="' + checkboxGroupName + '"]').changeValue(false);
            });
        });
    };
    
    // 5. scrollable-checkboxes render like a Bootstrap multiselect, but with checkboxes. I also refer to these as "scrollable checkbox areas".
    forms.scrollableCheckboxes = function() {
        // Adjust the content area height based on the data-size attribute.
        var size = $(".scrollable-checkboxes").data("size");
        $(".scrollable-checkboxes").height(size * 22);
        $(".scrollable-checkboxes > div").mousedown(function(e) {
            // Click an option to check a checkbox. If the element directly clicked is the checkbox itself, then do nothing, because the two checks would cancel out.
            $checkbox = $('input[type="checkbox"]', this);
            if (e.target != $checkbox[0]) {
                $checkbox.check();
            }
        });
        // If a checkbox inside the scrollable checkbox area is checked or unchecked by a script, highlight or unhighlight its option.
        $('.scrollable-checkboxes input[type="checkbox"]').change(function() {
            var isChecked = $(this).prop("checked");
            if (isChecked) {
                $(this).parent().addClass("selected");
            }
            else {
                $(this).parent().removeClass("selected");
            }
        });
        // If the scrollable checkbox area has a "Clear" button because it has a lot of options, then make it uncheck all the options when clicked.
        $('.scrollable-checkboxes .btn-primary').click(function() {
            var checkboxGroupName = $('input[type="checkbox"]',$(this).parent()).prop("name");
            $('input[type="checkbox"][name="' + checkboxGroupName + '"]').changeValue(false);
        });
    };
    
    
    // 6.1. Make sure that the custom checkbox is checked if the hidden default checkbox is checked.
    //     "this" should refer to the default checkbox, either through an event handler or .call().
    forms.adjustCustomCheckbox = function() {
        var $parent = $(this).parent();
        var isChecked = $(this).prop("checked");
        if (isChecked) {
            $("span, img",$parent).show();
        }
        else {
            $("span, img",$parent).hide();
        }
    };
    
    // 6. This function makes custom-styled checkboxes behave the same way as the default checkboxes. The default checkbox itself cannot be styled, so I
    //    wrapped it in a <div> and styled that instead. This function requires Bootstrap, only because the event handler is being attached to Bootstrap classes
    //    for the container of a checkbox and its label.
    //    
    //    Even though the default checkbox is hidden, the user still interacts with it by clicking it, so the custom checkbox will still fire the "change" event without .trigger("change").
    forms.customCheckboxes = function() {
        // When the page loads, hide all checkmarks for custom checkboxes, with two exception cases. First, keep showing checkmarks for checkboxes that have the Boolean [checked] attribute.
        // Second, when a form has been submitted, the user hits back, and the page reloads with the same data, checkboxes that the user checked before should still be checked. This is
        // especially important for a search form.
        $(".custom-checkbox").each(function() {
            if (!$('input[type="checkbox"]', this).prop("checked")) {
                $("span, img",this).hide();
            }
        });
        
        // Despite the default checkbox being hidden, it becomes checked when the user clicks its location. When this happens, check or uncheck the custom checkbox.
        $('.custom-checkbox input[type="checkbox"]').change(forms.adjustCustomCheckbox);
    };

    // 7. Make sure each checkbox with the attribute [data-dependent-on="NAME"] can only be checked when "NAME" is checked.
    //    When the dependent checkbox is checked, check the independent checkbox. When the independent checkbox is unchecked, uncheck the dependent checkbox.
    forms.dependentCheckboxes = function() {
        $("[data-dependent-on]").each(function() {
            var target = $(this).data("dependent-on");
            var $target = $('[name="' + target +'"]');
            var $dependent = $(this);
            // The script assumes that the dependent checkbox and the target checkbox were both unchecked or checked when the page loaded.
            $dependent.change(function () {
                var targetIsChecked = $target.prop("checked");
                var dependentIsChecked = $dependent.prop("checked");
                if (!targetIsChecked && dependentIsChecked) {
                    // Check the target checkbox, which makes its status the same as the dependent checkbox's status.
                    $target.check();
                }
            });
            $target.change(function () {
                var targetIsChecked = $target.prop("checked");
                var dependentIsChecked = $dependent.prop("checked");
                if (!targetIsChecked && dependentIsChecked) {
                    // Uncheck the dependent checkbox, which makes its status the same as the target checkbox's status.
                    $dependent.check();
                }
            });
        });
    };
    
    // 8. If a checkbox with the value "Any" is checked, check all checkboxes with the same name attribute. Keep the "Any" checkbox checked as long as all the other checkboxes stay checked.
    //    This function requires that there isn't any duplication of form controls, like a second copy with the same name, or else the script will only be applied to the last one.
    forms.anyCheckbox = function() {
        $('input[type="checkbox"][value="any"],input[type="checkbox"][value="Any"]').each(function() {
            var checkboxGroupName = $(this).prop("name");
            // If "Any" is checked, make all checkboxes checked.
            $(this).change(function() {
                var theAnyCheckboxIsChecked = $(this).prop("checked");
                if (theAnyCheckboxIsChecked) {
                    $('input[type="checkbox"][name="' + checkboxGroupName + '"]').changeValue(true); 
                }
            });
            // Uncheck this "Any" checkbox if it is currently checked, and any other checkbox with the same name attribute becomes unchecked.
            var $anyCheckbox = $(this);
            $('input[type="checkbox"][name="' + checkboxGroupName + '"]:not([value="any"]):not([value="Any"])').change(function() {
                var theAnyCheckboxIsChecked = $anyCheckbox.prop("checked");
                var thisIsChecked = $(this).prop("checked");
                if (theAnyCheckboxIsChecked && !thisIsChecked) {
                    $anyCheckbox.changeValue(false);
                }
            });
        });
    };
    
    // 9. This function changes the behavior of placeholder text so that it clears when the text field gains focus, instead of when the user begins typing in it.
    forms.clearPlaceholderTextOnFocus = function() {
        $("[placeholder]").each(function() {
            var placeholderText = $(this).attr("placeholder");
            $(this).focus(function() {
                $(this).attr("placeholder","");
            });
            $(this).blur(function() {
                $(this).attr("placeholder",placeholderText);
            })
        });
    }
    
    // 10.2 If the user presses enter while typing in the most recently created text field, add a new text field below it.
    //     Pressing enter in any of the earlier text fields will have no effect. This is a recursive function.
    var addNewTextFieldOnEnter = function() {
        $("table.form tr:has(span.add-field) input:last-child").keydown(function(e) {
            // If the user pressed "Enter"
            if (e.which == 13) {
                var $row = $(this).parent().parent();
                var $plusSign = $("span.add-field",$row);
                var $fieldCell = $(this).parent();
                // Create a new text field below this element.
                forms.addNewTextField($plusSign,$fieldCell);
                // Remove the event from this element.
                $(this).off("keydown");
                // Add the event to the new element.
                addNewTextFieldOnEnter();
                // Move the text cursor to the new element.
                $("table.form tr:has(span.add-field) input:last-child").focus();
            }
        });
    };
    
    // 10.1.1 Input: The <span class="add-field"> for the table row. The form table cell containing the first field. Using these as arguments will allow an event handler containing
    //    this function to first obtain the elements using "this" and a convenient path through the DOM. 
    //    Processing: Add a new text field to the form table cell.
    forms.addNewTextField = function($plusSign, $fieldCell) {
        var $fields = $fieldCell.children();
        var $lastField = $fields[$fields.length-1];
        // Obtain the attributes of the last field so that they can be copied to the next field.
        var lastFieldName = $($lastField).attr("name");
        var fieldType = $($lastField).attr("type");
        if (fieldType == "number") {
            var fieldMin = $($lastField).attr("min");
            var fieldMax = $($lastField).attr("max");
            var fieldStep = $($lastField).attr("step");
        }
        // Obtain the name of the field without the digits on the end.
        var fieldName = lastFieldName.match("^\\D+");
        // Obtain the number at the end of the last field's name.
        var lastFieldNumber = parseInt(lastFieldName.match("\\d+$"));
        // Generate the HTML for the next field, with the same attributes as the previous field except for the name.
        var nextFieldNumber = lastFieldNumber + 1;
        var nextFieldName = fieldName + nextFieldNumber.toString();
        var nextFieldHTML = '<br>' + '<input type="' + fieldType + '" name="' + nextFieldName + '"';
        if (fieldMin) {
            nextFieldHTML = nextFieldHTML + ' min="' + fieldMin + '"';
        }
        if (fieldMax) {
            nextFieldHTML = nextFieldHTML + ' max="' + fieldMax + '"';
        }
        if (fieldStep) {
            nextFieldHTML = nextFieldHTML + ' step="' + fieldStep + '"';
        }
        nextFieldHTML = nextFieldHTML + '>';
        $fieldCell.append(nextFieldHTML);
        // Move the plus sign down to the right of the newest field.
        $plusSign.css("top", "+=31px");
    };
    
    // 10.1 Upon clicking the plus sign in <th>, add a new text field to its adjcent table cell allowing multiple fields.
    var addNewTextFieldOnClick = function() {
        $("table.form th > span.add-field").click(function() {
            $plusSign = $(this);
            // Obtain the fields' cell and the last field by moving through the DOM, up from the <span class="plus"> to its parent <th>, over to an adjacent element, <td>,
            // and back down to <input>.
            var $fieldCell = $(this).parent().next();
            // Prevent this field from creating a new field on pressing Enter.
            $("table.form tr:has(span.add-field) input:last-child").off("keydown");
            forms.addNewTextField($plusSign,$fieldCell);
            // Allow pressing enter in the newest text field to create a new text field.
            addNewTextFieldOnEnter();
        });
    };
    
    // 10. In situations appropriate for one or more text field for one label, like social media URLs, allow the user to click a plus sign by a label to add another field.
    //    This function supports all HTML5 form controls which render as text fields when unsupported. In this HTML, use this function by placing <span class="add-field">+</span>
    //    before the table.form label.
    //    Requirements: 1. The field name must not contain any digits except at the end. The digits at the end of the field name must signify its order from the top, starting with 1.
    //                  2. The only attributes on the text field are assumed to be "name", "type", and possibly "min", "max", and "step".
    //                     (I left out "placeholder", because having it only on the first field will suffice to let the user know the data format, and it gets annoying if the same
    //                     placeholder is visible on two fields in a row.)
    //                  3. The plus sign is moved down at an increment that assumes text fields are 26px tall, including the padding and the border, and that the vertical margin between
    //                     multiple text fields in the same cell will be 5px. Adjust the increment if any of this changes in the sitewide CSS.
    //    Future improvements: Later during the project, when handling the backend, it may be appropriate to collect all the URLs in an array before submitting the form.
    //                         The first field would have no number at the end, so that the form would still work with JavaScript disabled and only one field.
    forms.oneOrMoreFields = function() {
        addNewTextFieldOnClick();
        addNewTextFieldOnEnter();
    };

   // 11.1, 11.4.1, 11.6.1  This function checks the Nth hidden radio button when the user interacts with the Nth visible button. If the widget is client-side-only, the function does nothing.
   // Input: selector, a string for the class used by the button the user interacts with, like ".radio-btn". Make sure "this" refers to the clicked element using .call(this,selector).
   forms.checkCorrespondingRadioButton = function(selector) {
       $parent = $(this).parent();
        // If there are radio buttons within the parent <div> of the pressed button,
        if ($('input[type="radio"]',$parent)) {
            // Obtain an array of only the .radio-btns within the parent <div>.
            var allButtons = $parent.children(selector).toArray();
            // Obtain the index of the pressed button within the array.
            var index = allButtons.lastIndexOf(this);
            // Obtain an array of only input[type="radio"] form controls within the parent <div>.
            var allRadio = $('input[type="radio"]',$parent).toArray();
            // Check the corresponding radio button. If the third .radio-btn is pressed, check the third input[type="radio"].
            var correspondingValue = $(allRadio[index]).val();
            $('input[type="radio"]',$parent).val([correspondingValue]).trigger("change");
        }
   };

   // 11.5, 11.3.1 This function checks the Nth hidden checkbox when the user interacts with the Nth visible button. If the widget is client-side-only, the function does nothing.
   //        Input: selector, a string for the class used by the button the user interacts with, like ".check-btn". Make sure "this" refers to the clicked element using .call(this,selector).
   forms.checkCorrespondingCheckbox = function(selector){
        $parent = $(this).parent();
        // If there are checkboxes within the parent <div> of the pressed button,
        if ($('input[type="checkbox"]',$parent)) {
            // Obtain an array of only the .check-btns within the parent <div>.
            var allButtons = $parent.children(".check-btn").toArray();
            // Obtain the index of the pressed button within the array.
            var index = allButtons.lastIndexOf(this);
            // Obtain an array of only input[type="checkbox"] form controls within the parent <div>.
            var allCheckboxes = $('input[type="checkbox"]',$parent).toArray();
            // Check the corresponding checkbox. If the third .check-btn is pressed, check the third input[type="checkbox"].
            var correspondingValue = $(allCheckboxes[index]).val();
            $('input[type="checkbox"][value="' + correspondingValue +'"]',$parent).check();
        }
   };
    
    // 11.3 This is a higher-order function which sets up the variables for image button behavior based on the file paths in the data- attributes. If the image button differs between day/night mode, it
    //     detaches events and re-attaches them with new values for the variables when the user toggles day/night mode. So, adding another widget to forms.buttonRadioAndCheckgroups() only requires writing
    //     another callback function which attaches all of its event handlers.
    //     Input:  callback, the function which attaches all the event handlers to the button.
    //             classSelector, a selector string for the class used by the widget, like ".rating-widget-btn". This is only needed for detaching events when the widget has night/day mode versions.
    //             When you invoke this function, make sure "this" refers to the element in the parent function's foreach loop by using .call(this,callback,classSelector).
    //     Output: Technically none, but the function determines $parent, widgetHasBeenClicked, activeIcon, and inactiveIcon and passes them to the callback function.
    //             $parent is the container of the buttons and whatever hidden form controls are checked.
    //             widgetHasBeenClicked is a flag used by form controls which have a hover effect only before the user clicks for the first time, like the rating widget.
    //             inactiveIcon and activeIcon are the strings for the paths used before and after the user clicks. Some image buttons also use activeIcon for hover effects.
    forms.setUpImageButtonBehavior = function(callback,classSelector) {
        // Gather all the variables for the rating widget.
        var $parent = $(this).parent();
        var widgetHasBeenClicked = false;
        
        if ($("img",this).is("[data-day-active]")) {
            // The rating widget has a day mode version and a night mode version. The selector "img[data-day-active]" will be used to identify images that are for the button itself and not the label.
            if (settings.layout["nightModeIsOn"]) {
                var activeIcon = $("img[data-day-active]",this).data("night-active");
                var inactiveIcon = $("img[data-day-active]",this).data("night-inactive");
            }
            else {
                var activeIcon = $("img[data-day-active]",this).data("day-active");
                var inactiveIcon = $("img[data-day-active]",this).data("day-inactive");
                // Day mode icons should be used when the page loads.
                $("img[data-day-active]",$parent).attr("src",inactiveIcon);
            }
            // Update the variables and paths if the user toggles night/day mode.
            $(window).on("toggleNightDay",function() {
                // I don't know why, but activeIcon and inactiveIcon are intially undefined in this event, even though $parent and widgetHasBeenClicked are.
                // It doesn't matter, because the value will be re-obtained.
                if (settings.layout["nightModeIsOn"]) {
                    // For all rating widget buttons which currently have src set to "day-active", set it to "night-active".
                    // For all rating widget buttons which currently have src set to "day-inactive", set it to "night-inactive".
                    $("img[data-day-active]",$parent).each(function() {
                        if ($(this).attr("src") == $(this).data("day-active")) {
                            $(this).attr("src", $(this).data("night-active"));
                        }
                        else {
                            $(this).attr("src", $(this).data("night-inactive"));
                        }
                    });
                    // Unlike last time, $parent is used because "this" is unavailable inside an event handler. Only the first matching element is used by .data(), so there is no effective difference.
                    var activeIcon = $("img[data-day-active]",$parent).data("night-active");
                    var inactiveIcon = $("img[data-day-active]",$parent).data("night-inactive");
                }
                else {
                    // For all rating widget buttons which currently have src set to "night-active", set it to "day-active".
                    // For all rating widget buttons which currently have src set to "night-inactive", set it to "day-inactive".
                    $("img[data-day-active]",$parent).each(function() {
                        if ($(this).attr("src") == $(this).data("night-active")) {
                            $(this).attr("src", $(this).data("day-active"));
                        }
                        else {
                            $(this).attr("src", $(this).data("day-inactive"));
                        }
                    });
                    // Unlike last time, $parent is used because "this" is unavailable inside an event handler. Only the first matching element is used by .data(), so there is no effective difference.
                    var activeIcon = $("img[data-day-active]",$parent).data("day-active");
                    var inactiveIcon = $("img[data-day-active]",$parent).data("day-inactive");
                }
                // Due to scope issues, if the widget was clicked prior to toggling, the widgetHasBeenClicked flag won't have changed.
                // Determine the status of the flag by looking at the src values of each button.
                $("img[data-day-active]",$parent).each(function() {
                    if ($(this).attr("src") == $(this).data("night-active") || $(this).attr("src") == $(this).data("day-active")) {
                        widgetHasBeenClicked = true;
                    }
                });
                // Detach the event handlers and re-attach them, so they can run again with the new variables. Remove any event that is used by any of the image button types.
                $parent.children(classSelector).off("mouseover").off("mouseenter").off("mouseleave").off("click");
                $parent.off("mouseover");
                callback($parent,widgetHasBeenClicked,activeIcon,inactiveIcon);
            });
        }
        else {
            // The rating widget uses the same files for both day mode and night mode. The selector "img[data-active]" will be used to identify images that are for the button itself and not the label.
            var activeIcon = $("img[data-active]",this).data("active");
            var inactiveIcon = $("img[data-active]",this).data("inactive");
        }
        callback($parent,widgetHasBeenClicked,activeIcon,inactiveIcon);
    };
    
    // 11.4 Attach the event handlers for the image radio button.
    forms.attachImageRadioButtonEventHandlers = function($parent, widgetHasBeenClicked, activeIcon, inactiveIcon) {
        // If widget hasn't been clicked yet and it supports alternate file paths, then use a hover effect.
        $("div.radio-btn",$parent).mouseenter(function() {
            if (!widgetHasBeenClicked && $("img[data-active], img[data-day-active]",this)[0]) {
                // Make this button have the active icon, but without any effects from .active.
                $("img[data-active], img[data-day-active]",this).attr("src",activeIcon);
            }
        });
        $("div.radio-btn",$parent).mouseleave(function() {
            if (!widgetHasBeenClicked && $("img[data-active], img[data-day-active]",this)[0]) {
                // Make this button appear inactive.
                $("img[data-active], img[data-day-active]",this).attr("src",inactiveIcon);
            }
        });
        $("div.radio-btn",$parent).click(function() {
            // Make this button appear active. If a pressed button is clicked again, nothing needs to happen.
            if (!$(this).hasClass("active")) {
                // Transfer the active status to the button that was clicked. Make only the clicked button have the .active class and active icon.
                $("div.radio-btn", $parent).removeClass("active");
                $(this).addClass("active");
                if ($("img[data-active], img[data-day-active]",this)[0]) {
                    $("img[data-active], img[data-day-active]",$parent).attr("src",inactiveIcon);
                    $("img[data-active], img[data-day-active]",this).attr("src",activeIcon);
                }
                
                widgetHasBeenClicked = true;
                forms.checkCorrespondingRadioButton.call(this,".radio-btn");
           }
        });
    };
    
    // 11.5 Attach the event handlers for the image check button.
    forms.attachImageCheckButtonEventHandlers = function($parent, widgetHasBeenClicked, activeIcon, inactiveIcon) {
        // Have a hover effect only if there are alternate file paths, and only while the image check button is inactive.
        // The hover effect toggles the inactive/active file path without toggling the active class.
        $("div.check-btn",$parent).mouseenter(function() {
            if ($("img[data-active], img[data-day-active]",this)[0] && !$(this).hasClass("active")) {
                $("img[data-active], img[data-day-active]",this).attr("src",activeIcon);
            }
        });
        $("div.check-btn",$parent).mouseleave(function() {
            if ($("img[data-active], img[data-day-active]",this)[0] && !$(this).hasClass("active")) {
                $("img[data-active], img[data-day-active]",this).attr("src",inactiveIcon);
            }
        });
        
        $("div.check-btn",$parent).click(function() {
            $(this).toggleClass("active");
            // If the image check button has alternate file paths, toggle them as well.
            if ($("img[data-active], img[data-day-active]", this)[0]) {
                if ($(this).hasClass("active")) {
                    $("img[data-active], img[data-day-active]", this).attr("src", activeIcon);
                }
                else {
                    $("img[data-active], img[data-day-active]", this).attr("src", inactiveIcon);
                }
            }
            widgetHasBeenClicked = true;
            forms.checkCorrespondingCheckbox.call(this,".check-btn");
        });
    };
    
    // 11.6 Provide a rating on a scale of 1 to N. Mousing over an icon makes the icons appear the same as when the icon's option has been clicked.
    //     For example, mousing over the third star in a five-star ratings widget fills the first, second, and third star while leaving the fourth and fifth empty.
    //     When the user stops mousing over any of the icons, they all appear inactive again. The file paths should be the same for each rating widget button in the group.
    //     So that the mouseover effect is continuous, the borders of each rating widget button should all be touching.
    
    //     The HTML structure is the same as for image buttons, and the images use the same data- attributes. The script checks hidden radio buttons listed after the image buttons.
    //     <div class="rating-widget">
    //        <img>
    //        Label
    //     </div>
    //
    //     The rating widget is mostly used for submitting new data to the server. When looking up data in the search engine, use image check buttons with the same file paths.
    forms.attachRatingWidgetEventHandlers = function($parent,widgetHasBeenClicked,activeIcon,inactiveIcon) {
        $(".rating-widget-btn",$parent).mouseover(function() {
            if (!widgetHasBeenClicked) {
                // Make this button and all its previous siblings appear active.
                $("img[data-active], img[data-day-active]",this).attr("src",activeIcon);
                $(this).prevAll(".rating-widget-btn").find("img[data-active], img[data-day-active]").attr("src",activeIcon);
                // Make all the next siblings appear inactive.
                $(this).nextAll(".rating-widget-btn").find("img[data-active], img[data-day-active]").attr("src",inactiveIcon);
            }
        });
        $parent.mouseover(function(e) {
            // If the user's cursor has left all of the rating widget buttons and none of them has been clicked yet, then make them all appear inactive.
            // The first part of the condition makes this effectively the same as a mouseleave event for multiple touching elements.
            if (!$(e.target).closest(".rating-widget-btn")[0] && !widgetHasBeenClicked) {
                $(".rating-widget-btn img[data-active], .rating-widget-btn img[data-day-active]",$parent).attr("src",inactiveIcon);
            }
        });
        $(".rating-widget-btn",$parent).click(function() {
            // Make this button and all its previous siblings appear active.
            $("img[data-active], img[data-day-active]",this).attr("src",activeIcon);
            $(this).prevAll(".rating-widget-btn").find("img[data-active], img[data-day-active]").attr("src",activeIcon);
            // Make all the next siblings appear inactive.
            $(this).nextAll(".rating-widget-btn").find("img[data-active], img[data-day-active]").attr("src",inactiveIcon);
            widgetHasBeenClicked = true;
            forms.checkCorrespondingRadioButton.call(this,".rating-widget-btn");
        });
    };
    
   // 11. "Bootstrap check buttons", "Bootstrap radio buttons", "image check buttons", "image radio buttons", and "image buttons" are the terms I use to refer to the widgets this function scripts.
   //     This function is for Bootstrap buttons or images which, when clicked or touched ("pressed"), check hidden form controls. Bootstrap has this built-in, but it only works for button groups. When an image
   //     button is clicked, it can change the styling around the image (like a border for highlighting) or switch between file paths. Note that this function doesn't toggle an image representing a check on/off;
   //     this style is covered by other functions. If the form control is for client-side effects only, then you can choose to omit the default form controls from the HTML source code. Other scripts will know
   //     which element is checked by looking for certain classes and attributes. 
   
   //     When replacing a checkbox or some sort of multiselect, hidden checkboxes are listed in the HTML source code after the pressable elements. When replacing a set of radio buttons or a <select> dropdown,
   //     hidden radio buttons are listed in the HTML source code after the pressable elements.
   // 
   //     1. The .check-btn class makes a button stay pressed until it is clicked or touched again.
   //        If you are using a Bootstrap button and the effect is client-side only, then you can use Bootstrap's [data-toggle="button"] instead.
   //     2. The .radio-btn class makes a button stay pressed when clicked or touched, while also unpressing all other buttons in the set (parent <div>).
   //     3. .check-btn and .radio-btn are pressed if they have the .active class. In the HTML source code, every form control with a checked attribute should have .active on the corresponding button.
   //     4. The .rating-widget class also uses radio buttons, but with different effects. If you mouseover the third button (e.g. a star), it fills the first, second, and third stars.
   //        These currently do not use the .active class.
   // 
   //     Image buttons have the attributes src, data-active, and data-inactive. If the image button has a day/night mode version (because it is black/white and might not show up well), then it has the attributes
   //     src, data-active, and data-inactive. These alternate paths are optional; an image button may use only one path and have its selection indicated by styling .active instead.
   //     If there are active/inactive paths, then the image check buttons have a hover effect. They appear active on mouseover, and on click the change is made permanent. Image radio buttons with active/inactive
   //     paths will have a hover effect only until the first click, because it might be confusing if two options appeared active at once.
   // 
   //     HTML structure an for image button: Each image button uses an inline-block <div> with cursor: pointer. The first-child is <img>. Optionally, text or anything else for labeling can be placed below it.
   //     <div class="radio-btn active">
   //         <img>
   //         Label
   //     </div>
      
   //     Currently, the JavaScript supports falling back to regular form controls if JavaScript is disabled, but I haven't supported it in the CSS.
    forms.buttonRadioAndCheckgroups = function() {
        // Set up each Bootstrap radio button group.
        $("button.radio-btn").click(function() {
            // If a pressed button (one with the .active class) is clicked again, nothing needs to happen.
            if (!$(this).hasClass("active")) {
                $parent = $(this).parent();
                // Transfer the .active class to the button that was clicked.
                $("button.radio-btn", $parent).removeClass("active");
                $(this).addClass("active");
                
                forms.checkCorrespondingRadioButton.call(this,".radio-btn");
           }
        });
        // Set up each Bootstrap check button group.
        $("button.check-btn").click(function() {
            $(this).toggleClass("active");
            forms.checkCorrespondingCheckbox.call(this,".check-btn");
        });
        
        // Set up each image button radio group.
        $('div.radio-btn:first-of-type').each(function() {
            forms.setUpImageButtonBehavior.call(this,forms.attachImageRadioButtonEventHandlers,".radio-btn");
        });
        // Set up each image button check group.
        $('div.check-btn:first-of-type').each(function() {
            forms.setUpImageButtonBehavior.call(this,forms.attachImageCheckButtonEventHandlers,".check-btn");
        });
        // Set up each rating widget.
        $('.rating-widget-btn:first-of-type').each(function() {
            forms.setUpImageButtonBehavior.call(this,forms.attachRatingWidgetEventHandlers,".rating-widget-btn");
        });
    };
    
    // 12. This function is necessary for the custom file browse button to work in IE11, but not IE9 or IE10. See scrapbin.css for the documentation.
    forms.customFileBrowseButton = function() {
        IEVersion = browserInvestigator.detectIEVersion();
        // Target IE11 only, or else other browsers will open the file picker a second time after closing it.
        if (IEVersion == 11) {
            $(document).on('click', '.custom-file-browse > :first-child', function() {
                $(this).next().click();
            });
        };
    };
    
    // 13.1 For each "same as" checkbox, toggle whether its target fields are readonly. The readonly fields will have the text hidden so that the user can more easily concentrate on the other fields.
    // In the style sheet, the readonly fields must be styled as greyed out, or else the fields will mistakenly appear blank.
    forms.toggleReadonlyTargetFields = function() {
        targetNames = $(this).data("target-fields").split(", ");
        for (var i = 0; i < targetNames.length; i++) {
            $targetFormControl = $('[name="'+targetNames[i]+'"]');
            if ($(this).prop("checked")) {
                $targetFormControl.attr("readonly", true);
                $targetFormControl.css("color", "rgba(0,0,0,0)"); // Hide the text of the readonly fields.
            }
            else {
                $targetFormControl.attr("readonly", false);
                $targetFormControl.css("color", "");
            }
        }
    };
    
    // 13.2 For each "same as" checkbox, copy the values from its source fields to its target fields. Then, submit the form.
    forms.copySameAsValuesAndSubmit = function(e) {
        e.preventDefault();
        $("[data-source-fields]", $(this)).each(function() {
            if ($(this).prop("checked")) {
                sourceNames = $(this).data("source-fields").split(", ");
                targetNames = $(this).data("target-fields").split(", ");
                for (var i=0; i < targetNames.length; i++) {
                    $sourceFormControl = $('[name="'+sourceNames[i]+'"]');
                    $targetFormControl = $('[name="'+targetNames[i]+'"]');
                    sourceValue = $('[name="'+sourceNames[i]+'"]').val();
                    // Set the target form control's value as the source form control's value.
                    $('[name="'+targetNames[i]+'"]').val(sourceValue);
                }
            }
        });
        this.submit();
    };
    
    // 13. This function scripts a checkbox which, when checked, will copy values from a set of fields into another set of fields.
    // HTML: <input type="checkbox" data-source-fields="" data-target-fields=""/> Use a comma-separated list of the names of the fields.
    // This function only works for text fields, HTML5 fields which render as text fields in old browsers, and <select>s.
    forms.sameAsCheckbox = function() {
        $("[data-source-fields]").on("change", forms.toggleReadonlyTargetFields);
        $('form:has([data-source-fields])').on("submit", forms.copySameAsValuesAndSubmit);
    };
    
    // 14. In this scenario, a yes/no question with radio buttons has another question, within the same <div class="field">, that is hidden.
    //     Display the hidden question, contained in an element with the class "follow-up", if "yes" is checked.
    forms.prepareYesNoFollowUps = function() {
        $(".follow-up").hide();
        $('.field:has(.follow-up) input[type="radio"]').change(function() {
            $field = $(this).closest(".field");
            var value = $(this).val().toLowerCase();
            if (value == "yes") {
                $(".follow-up",$field).show();
            }
            else {
                $(".follow-up",$field).hide();
            }
        });
    };
    
    // 15. This function is for a container of form fields that are hidden until certain options are selected in other form controls above it. See the CSS file for example HTML.
    forms.nestedForms = function() {
        $(".nested-form").each(function() {
            $(".collapse", $(this)).on("show.bs.collapse", function() {
                // When any field inside the .nested-form is shown, then .nested-form is shown.
                $(this).parent().show();
            });
            $(".collapse", $(this)).on("hidden.bs.collapse", function() {
                if (!$(".in", $(this).parent())[0]) {
                    // When the last visible field is hidden, then .nested-form is hidden.
                    $(this).parent().hide();
                }
            });
        });
    };
    
    // 16. This function styles a "Today" button to the right of a date form control and a "Now" button to the right of a time form control.
    forms.todayAndNowButtons = function() {
        $('input[type="date"]+button').click(function() {
            // If the browser has a date picker, then setting the value of the field will require the standard format, which will be rendered as MM/DD/YYYY regardless.
            // If the browser doesn't have a date picker, then use MM/DD/YYYY to format the value so that it will render that way. This function assumes the format doesn't matter on the back end.
            if (Modernizr.inputtypes.date) {
                today = moment().format('YYYY-MM-DD');
            }
            else {
                today = moment().format('MM/DD/YYYY');
            }
            $(this).prev().val(today);
        });
        $('input[type="time"]+button').click(function() {
            // If the browser has a time picker, then setting the value of the field will require the standard format, which will be rendered like "08:53 PM" regardless.
            // If the browser doesn't have a time picker, then use the "08:53 PM" pattern to format the value so that it will render that way. This function assumes the format doesn't matter on the back end.
            if (Modernizr.inputtypes.date) {
                current_time = moment().format('HH:mm');
            }
            else {
                current_time = moment().format('hh:mm A');
            }
            $(this).prev().val(current_time);
        });
    };
    
    // 0. Main function
    var main = function() {
        forms.searchIconsSubmit(); // 1
        forms.consistentFormTableColumnWidths(); // 2
        forms.keyboardlessMultiselects(); // 3
        forms.checkboxDropdowns(); // 4
        forms.scrollableCheckboxes(); // 5
        forms.customCheckboxes(); // 6
        forms.dependentCheckboxes(); // 7
        forms.anyCheckbox(); // 8
        forms.clearPlaceholderTextOnFocus(); // 9
        forms.oneOrMoreFields(); // 10
        forms.buttonRadioAndCheckgroups(); // 11
        forms.customFileBrowseButton(); // 12
        forms.sameAsCheckbox(); // 13
        forms.prepareYesNoFollowUps(); // 14
        forms.nestedForms(); // 15
        forms.todayAndNowButtons(); // 16
    };
    main();
});