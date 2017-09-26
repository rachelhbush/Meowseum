/* Description: This file contains functions that make it easier to implement widgets which are dependent on AJAX. It is dependent on jQuery and the jQuery Form Plugin API. */

$(document).ready(function() {
    // Create a namespace for the sitewide AJAX functions.
    window.ajax = window.ajax || {};
    
    // A.3. Test that a given url is a same-origin URL. The URL could be relative, scheme relative, or absolute.
    var sameOrigin = function(url) {
            var host = document.location.host; // host + port
            var protocol = document.location.protocol;
            var sr_origin = '//' + host;
            var origin = protocol + sr_origin;
            // Allow absolute or scheme relative URLs to same origin
            return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
   };
    
    // A.2. Return whether the HTTP method is one which does not require CSRF protection.
    var csrfSafeMethod = function(method) {
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    };
    
    // A.1. This function gets the cookie with a given name.
    var getCookie = function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
    
    // A. This library function is invoked by every Django AJAX function. It implements CSRF protection without having to include a CSRF token in the HTML. The function allows AJAX requests from elements that are not nested
    // inside a <form>, which makes coding the layout easier as long as the developer is willing to skip support for users with JavaScript disabled. See the Django documentation for an explanation of how it works:
    // https://docs.djangoproject.com/en/1.11/ref/csrf/
    ajax.setupXCSRFTokenHeader = function() {
        var csrftoken = getCookie('csrftoken');
        // Create a header with the csrftoken.
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                    // Send the token to same-origin, relative URLs only.
                    // Send the token only if the method warrants CSRF protection
                    // Using the CSRFToken value acquired earlier
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    };
    
    // B. This library function improves on jQuery's $.post() function in several ways. First, it handles Django's CSRF token. Second, if a server error occurs, it sends the error to the development console.
    // Third, it supplies a standard way for the server to indicate that the JavaScript should redirect the user to another URL, by using the JSON object {'status':0, 'message': "Redirecting", 'url':url}.
    // Input: url, data, success, dataType. The last three arguments are optional.
    // The success callback can be entered as the second argument without supplying data to the server.
    // Output: None
    ajax.post = function(url, arg2, arg3, dataType) {
            ajax.setupXCSRFTokenHeader();
            
            var options = {
                "url": url,
                "type": "POST",
                "error": function(xhr, errmsg, err){
                    // This is the function which handles a non-successful response.
                    // When the server has debug mode turned on, this will send the error log, which the developer usually sees in-browser, to the JavaScript development console.
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            };
            
            if (arguments.length == 2) {
                if (Object.prototype.toString.call(arg2) == "[object Function]") {
                    options["success"] = function(response, textStatus, jqXHR) {
                            // This is the function which handles a successful response. Depending on the response, it will either redirect the user or it will invoke the "success" function object.
                            var type = typeof response;
                            // Check whether the response is a JSON object containing a URL for redirecting.
                            if (type == 'object' && response.status != 1 && 'url' in response) {
                                // Redirect the user to the specified URL.
                                location.assign(response.url);
                            } else {
                                arg2.apply(null,arguments);
                            }
                    };
                }
                else {
                    options["data"] = arg2;
                }
            }
            if (arguments.length >= 3 && Object.prototype.toString.call(arg2) != "[object Function]") {
                options["success"] = function(response, textStatus, jqXHR) {
                            // This is the function which handles a successful response. Depending on the response, it will either redirect the user or it will invoke the "success" function object.
                            var type = typeof response;
                            // Check whether the response is a JSON object containing a URL for redirecting.
                            if (type == 'object' && response.status != 1 && 'url' in response) {
                                // Redirect the user to the specified URL.
                                location.assign(response.url);
                            } else {
                                arg3.apply(null,arguments);
                            }
                    };
            }
            if (arguments.length >= 4) {
                options["dataType"] = dataType;
            }
            
            $.ajax(options);
    };
    
    // C.2. Input: An element which the user clicks to send its name, value, data-name, and data-value values to the server.
    // Output: A JSON object. Its keys are from name and data-name and its values are from value and data-value.
    var getDataFromButtonAttributes = function(element) {
        // Create an empty JSON object into which the function will collect data to be sent to the server from various sources. $.ajax() will turn it into a querystring before sending it to the server.
        var data = {};
        
        if ($(element).attr("name") != undefined) {
            // Retrieve the data to be sent to the server from the name attribute.
            data[$(element).attr("name")] = $(element).attr("value");
        }
        if ($(element).data("name") != undefined) {
            // Retrieve the data to be sent to the server from the data-name attribute.
            var name_array = $(element).data("name").split(",");
            var value_array = $(element).data("value").split(",");
            for (var i=0; i < name_array.length; i++) {
                // Strip any space left of each comma-separated name and value.
            	if (name_array[i].charAt(0) == " ") {
                    name_array[i] = name_array[i].substring(1, name_array.length);
                }
            	if (value_array[i].charAt(0) == " ") {
                    value_array[i] = value_array[i].substring(1, name_array.length);
                }
                data[name_array[i]] = value_array[i];
            }
        }
        
        return data;
    };
    
    // C.1. Input: An element which the user clicks to communicate to the server to send data solely from its own attributes.
    // The function will retrieve the URL from data-ajax-url attribute on the clickable element. If this attribute is absent, the function falls back to retrieving the URL
    // from the element's closest <form> ancestor.
    // Output: URL string
    var getURLFromAttributes = function(element) {
        var url = $(element).data("ajax-url");
        if (url == undefined) {
            $form = $(element).closest("form");
            url = $form.attr("action");
        }
        return url;
    };
    
    // C. This AJAX method is a higher order function for an element which is the only element in a form, aside from Django's CSRF token. The element has all the data in name, value, data-name,
    // or data-value attributes, or the element has its own view for processing so no data is necessary. The element can be a button, but it can also be something like a Bootstrap dropdown option.
    // The element is wrapped in a <form> for compatibility with JavaScript being disabled. The method submits to the path specified by data-ajax-url and, without it, defaults to the same path as the
    // form's action attribute. Using a separate page for AJAX allows saving computation time by not re-rendering the whole page. The element will submit the data when clicked using the POST method and
    // then execute the callback function. data-name and data-value allow a comma-separated series of values, as in 'data-name="name1, name2"'.
    $.fn.submitOwnDataOnClickThen = function(success) {
        $(this, "form").click(function(e) {
            e.preventDefault();
            
            url = getURLFromAttributes(this);
            data = getDataFromButtonAttributes(this);
            ajax.post(url, data, success);
        });
    };
    
    // D. This is a library function which is used when the server responds with a JSON object in which keys consist of jQuery selectors and values consist of HTML
    // snippets to load into each corresponding jQuery set. The built-in .load() method is useful for loading HTML within a single frame like a modal, but this function is more useful for
    // interactions which insert HTML into multiple places throughout the DOM.
    //
    // When I use this, most of my selectors are classes, because elements that are otherwise unique may have a hidden duplicate for the sake of responsiveness.
    ajax.loadAJAXHTML = function(response) {
        var type = typeof response;
        if (type == 'object') {
            for (var property in response) {
                if (response.hasOwnProperty(property)) {
                    var selector = property;
                    var HTML_to_load = response[selector];
                    $(selector).html(HTML_to_load);
                }
            }
        }
    };
    
    // 2. This function sets the behavior for .ajax-btn, a custom class which indicates the element sends data to the server using name, value, data-name, and/or data-value
    // and then uses a JSON object to insert HTML into the DOM.
    ajax.loadButtons = function() {
        $(".ajax-btn").submitOwnDataOnClickThen(ajax.loadAJAXHTML);
    };
    
    // 1.1. After submitting a form in a modal, this function will load the response as HTML. To instruct the function to redirect to another page (the whole page, not the frame of the modal),
    // have the server return the JSON object {'status':0, 'message': "Redirecting", 'url':url}.
    var showResponse = function(response, statusText, xhr, $form) {
        var type = typeof response;
        // Check whether the response is a JSON object containing a URL for redirecting.
        if (type == 'object' && response.status != 1 && 'url' in response) {
            // Redirect the user to the specified URL.
            location.assign(response.url);
        } else {
            var $ajaxModal = $form.closest(".ajax-modal");
            $ajaxModal.html(response);
        }
    };
    
    // 1. This function sets up the behavior for .ajax-modal, which goes on .modal. The Bootstrap modal will use data-ajax-url to load its HTML content as soon as it is shown.
    // This is useful for forms in modals. It prevents having to store the form into a variable on every page, and it allows notifying the user of input errors without refreshing the page,
    // which hides the modal. If the server encounters an error, it will show the usual error page within the modal.
    // The function relies on jQuery Form Plugin (http://jquery.malsup.com/form/#ajaxSubmit), which uses a lengthy iframe workaround to implement submitting a file with AJAX.
    // IE10+ support the HTML5 File API which permits sending a file without the plugin, so once IE9 popularity falls enough for it to be dropped, this function should be rewritten to avoid using it.
    ajax.setupModals = function() {
        $(".ajax-modal").on("show.bs.modal", function() {
            var url = $(this).data("ajax-url");
            $(this).load(url);
        });
        // When the user tries to submit a form in an AJAX modal, submit the form via AJAX instead. If the response is a redirect, then JavaScript will redirect the user.
        // If the response is HTML, then load the HTML into the modal.
        $(".ajax-modal").on("submit", "form", function(e) {
            e.preventDefault();
            var options = {
                success: showResponse  // post-submit callback
            };
            $(this).ajaxSubmit(options);
        });
    };
    
    // 0. Main function
    var main = function(){
        ajax.setupModals();
        ajax.loadButtons();
    };
    main();
});