# Description: Toggle night/day mode. This is the page for processing an AJAX request from clicking the night/day option in a settings menu.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import urlencode

# 0. Main function.
def page(request):
    if request.is_ajax():
        night_mode = update_database(request)
        response_data = get_response_data(night_mode)
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        update_database(request)
        return HttpResponseRedirect(reverse('index'))

# 1. Toggle night mode in the database.
# Input: request
# Output: night_mode, a Boolean value for whether night mode is on after toggling
def update_database(request):
    if request.user.is_authenticated():
        viewer = request.user.user_profile
        if viewer.night_mode:
            viewer.night_mode = False
        else:
            viewer.night_mode = True
        viewer.save()
        return viewer.night_mode
    else:
        # If the user isn't registered, use session storage.
        if 'night_mode' in request.session:
            if request.session['night_mode']:
                request.session['night_mode'] = False
            else:
                request.session['night_mode'] = True
        else:
            # Night mode is the site default, so the first time the user toggles it, turn it off.
            request.session['night_mode'] = False
        return request.session['night_mode']

# 2. When night mode is toggled on, day mode HTML snippets will replace night mode HTML snippets in the settings menus and vice versa.
# This function will be written after update_database() has been tested and verified to work, because it may require dismantling the JavaScript in order to test it.
# Input: night_mode, Boolean.
# Output: Dictionary in which the keys are selectors and the values are HTML snippets which AJAX will insert into selected elements.
def get_response_data(night_mode):
    response_data = {}
    return response_data
