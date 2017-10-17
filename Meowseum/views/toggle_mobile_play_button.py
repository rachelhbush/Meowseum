# Description: Toggle night/day mode. This is the page for processing an AJAX request from clicking the night/day option in a settings menu.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import redirect, ajaxWholePageRedirect
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
from django.contrib.staticfiles.templatetags.staticfiles import static
import json
from Meowseum.context_processors import get_night_mode_status

# 0. Main function.
def page(request):
    if request.is_ajax():
        mobile_GIFs_are_playing = update_database(request)
        night_mode = get_night_mode_status(request)
        response_data = get_response_data(mobile_GIFs_are_playing, night_mode)
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        update_database(request)
        return redirect('index')

# 1. Toggle night mode in the database.
# Input: request
# Output: mobile_GIFs_are_playing, a Boolean value for whether mobile GIFs will be playing after toggling.
def update_database(request):
    if 'mobile_GIFs_are_playing' in request.session and not request.session['mobile_GIFs_are_playing']:
        request.session['mobile_GIFs_are_playing'] = True
    else:
        # GIFs automatically playing on mobile devices is the site default, so the first time the user toggles it, turn it off.
        request.session['mobile_GIFs_are_playing'] = False
    return request.session['mobile_GIFs_are_playing']

# 2. When night mode is toggled on, day mode HTML snippets will replace night mode HTML snippets in the settings menus and vice versa.
# This function will be written after update_database() has been tested and verified to work, because it may require dismantling the JavaScript in order to test it.
# Input: night_mode, Boolean.
# Output: Dictionary in which the keys are selectors and the values are HTML snippets which AJAX will use to replace the content of selected elements.
def get_response_data(mobile_GIFs_are_playing, night_mode):
    response_data = [{'selector': '#portrait-smartphone-icons #play-toggle, #landscape-smartphone-or-wider-icons #play-toggle'}]
    if mobile_GIFs_are_playing:
        if night_mode:
            src_attribute = static('images/Pause Icon - White.png')
        else:
            src_attribute = static('images/Pause Icon.png')
        response_data[0]['HTML_snippet'] = mark_safe('<img src="' + src_attribute + '" data-night="' + static('images/Pause Icon - White.png') + \
                                                   '" data-day="' + static('images/Pause Icon.png') + '" alt="Pause Icon" class="mobile-icon">')
    else:
        if night_mode:
            src_attribute = static('images/Play Icon - White.png')
        else:
            src_attribute = static('images/Play Icon.png')
        response_data[0]['HTML_snippet'] = mark_safe('<img src="' + src_attribute + '" data-night="' + static('images/Play Icon - White.png') + \
                                                   '" data-day="' + static('images/Play Icon.png') + '" alt="Play Icon" class="mobile-icon">')
    return response_data
