# Description: Mute or unmute action. This is the page for processing a request from a slide page's Follow button's Mute option, using the URL "user/username/mute".
# Currently, this is only for AJAX requests, but it is designed to handle requests when JavaScript is disabled.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import redirect, ajaxWholePageRedirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import json

def page(request, username):
    # The user can navigate to this page from the slide page, the user page (in the future), or the URL bar. The first two pages redirect to this page with a querystring.
    # when JavaScript is disabled, then this page redirects back. When redirecting occurs, redirect to the user page when the previous URL is unknown.
    previous_URL = request.GET.get('next', reverse('gallery', args=[username]))
    if request.user.is_authenticated():
        uploader_user = get_object_or_404(User, username=username)
        uploader = uploader_user.user_profile
        viewer = request.user.user_profile

        if viewer in uploader.muters.all():
            uploader.muters.remove(viewer)
            response_data = [{}]
            response_data[0]['selector'] = '.dropdown_mute_option'
            response_data[0]['HTML_snippet'] = mark_safe('<span class="glyphicon glyphicon-ban-circle"></span>Mute all activity')
        else:
            uploader.muters.add(viewer)
            # In Meowseum's current system, muting silences all activity. A user cannot be muted and followed at the same time. When either status is added, the other needs to be removed.
            uploader.followers.remove(viewer)
            response_data = [{},{},{}]
            response_data[0]['selector'] = '.dropdown_mute_option'
            response_data[0]['HTML_snippet'] = mark_safe('<span class="glyphicon glyphicon-ban-circle"></span>Unmute all activity')
            response_data[1]['selector'] = '.follow_button'
            response_data[1]['HTML_snippet'] = 'Follow'
            response_data[2]['selector'] = '.dropdown_follow_option'
            response_data[2]['HTML_snippet'] = 'Follow'

        if request.is_ajax():
            # If the request is AJAX, then respond with a JSON object containing the new Follow button label, the new label for the Follow option in its dropdown, and the new label for the
            # Mute option in its dropdown.
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return redirect(previous_URL)
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the previous page after the user logs in.
        return ajaxWholePageRedirect(request, 'login', query = 'next=' + previous_URL)
