$(document).ready(function() {
    // 1.1 Turn on disabling attributes and classes for the video fields.
    var disableVideoFields = function() {
        $('input[name="min_duration"], input[name="max_duration"], input[name="min_fps"]').prop("disabled", true);
        $('input[name="min_duration"], input[name="min_fps"]').closest("tr").addClass("disabled");
    };
    
    // 1.2 Remove disabling attributes and classes for the video fields.
    var enableVideoFields = function(){
        $('input[name="min_duration"], input[name="max_duration"], input[name="min_fps"]').prop("disabled", false);
        $('input[name="min_duration"], input[name="min_fps"]').closest("tr").removeClass("disabled");
    };
    
    // 1. When the user is filtering the search down to only Photos, grey out the fields that are only relevant to video files, put a not-allowed cursor over the whole area,
    // and use the disabled attribute to prevent these fields' values from being sent to the server.
    var disableVideoFieldsWhenSearchingForPhotos = function() {
        $('input[type="checkbox"][name="filter_by_photos"], input[type="checkbox"][name="filter_by_gifs"], input[type="checkbox"][name="filter_by_looping_videos_with_sound"]').change(function() {
            if ($('input[type="checkbox"][name="filter_by_photos"]').prop("checked")) {
                if (!$('input[type="checkbox"][name="filter_by_gifs"]').prop("checked") && !$('input[type="checkbox"][name="filter_by_looping_videos_with_sound"]').prop("checked")) {
                    disableVideoFields();
                }
                else {
                    enableVideoFields();
                }
            }
            else {
                enableVideoFields();
            }
        });
    };
    
    // 0. Main function
    var main = function() {
        disableVideoFieldsWhenSearchingForPhotos();
    };
    main();
});