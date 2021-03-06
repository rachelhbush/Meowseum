# Description: Toggle night/day mode. This is the page for processing an AJAX request from clicking the night/day option in a settings menu.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import redirect, ajaxWholePageRedirect
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
from django.contrib.staticfiles.templatetags.staticfiles import static
import json

# 0. Main function.
def page(request):
    if request.is_ajax():
        night_mode = update_database(request)
        response_data = get_response_data(night_mode)
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        update_database(request)
        return redirect('index')

# 1. Toggle night mode in the database.
# Input: request
# Output: night_mode, a Boolean value for whether night mode is on after toggling.
def update_database(request):
    if 'night_mode' in request.session and not request.session['night_mode']:
        request.session['night_mode'] = True
    else:
        # Night mode is the site default, so the first time the user toggles it, turn it off.
        request.session['night_mode'] = False
    return request.session['night_mode']

# 2. When night mode is toggled on, day mode HTML snippets will replace night mode HTML snippets in the settings menus and vice versa.
# This function will be written after update_database() has been tested and verified to work, because it may require dismantling the JavaScript in order to test it.
# Input: night_mode, Boolean.
# Output: Dictionary in which the keys are selectors and the values are HTML snippets which AJAX will use to replace the content of selected elements.
def get_response_data(night_mode):
    response_data = [{'selector': '.toggle-night-day'}]
    if night_mode:
        response_data[0]['HTML_snippet'] = mark_safe('Night mode<img src="' + static('images/Moon Icon - White.png') + '" alt="Moon icon">')
    else:
        response_data[0]['HTML_snippet'] = mark_safe('Day mode<img src="' + static('images/Sun Icon.png') + '" alt="Sun icon">')
    return response_data
