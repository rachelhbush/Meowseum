# Description: Follow or unfollow action. This is the page for processing a request to a follow a user. The request will be from a slide page's Follow button, from a dropdown
# option on a user's gallery page, or via the URL bar.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import json

# 0. Main function.
def page(request, username):
    # When JavaScript is disabled, the various pages redirect to this page, and this page redirects back.
    # Redirect to the user uploads gallery page when the previous URL is unknown.
    previous_URL = request.GET.get('next', reverse('gallery', args=[username]))
    if request.user.is_authenticated():
        uploader_user = get_object_or_404(User, username=username)
        follow_or_unfollow(request.user, uploader_user)

        if request.is_ajax():
            # The AJAX response will differ depending on the previous page.
            if '/slide/' in previous_URL or '/profile/' in previous_URL:
                response_data = get_follow_button_response(request.user, uploader_user)
            else:
                response_data = get_follow_option_in_dropdown_header_response(request.user, uploader_user, username)
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return redirect(previous_URL)
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the previous page after the user logs in.
        return ajaxWholePageRedirect(request, reverse('login') + "?next=" + previous_URL)

# 1. Update the followed/unfollowed status of the uploader.
# Input: request_user, a record for the User making the request. uploader_user, a record for the User who contributed the upload.
# Output: None.
def follow_or_unfollow(request_user, uploader_user):
    if request_user.user_profile in uploader_user.user_profile.followers.all():
        uploader_user.user_profile.followers.remove(request_user.user_profile)
    else:
        # In Meowseum's current system, muting silences all activity. A user cannot be muted and followed at the same time. When either status is added, the other needs to be removed.
        uploader_user.user_profile.followers.add(request_user.user_profile)
        uploader_user.user_profile.muters.remove(request_user.user_profile)
    uploader_user.user_profile.save()

# 2. Put together the AJAX response data for when the previous page has a Follow button.
# The response_data has a different structure than for get_follow_button_response() because I'm in the middle of reorganizing. It works for the button itself because the
# dropdown header uses a different class and JavaScript function, but the Follow option in the dropdown menu is broken.
# Input: request_user, uploader_user. Output: response_data
def get_follow_button_response(request_user, uploader_user):
    if request_user.user_profile in uploader_user.user_profile.followers.all():
        response_data = [{},{},{}]
        response_data[0]['selector'] = '.follow_button'
        response_data[0]['HTML_snippet'] = mark_safe('<span class="default-content">Following</span><span class="rollover-content">Unfollow</span>')
        response_data[1]['selector'] = '.dropdown_follow_option'
        response_data[1]['HTML_snippet'] = 'Unfollow'
        response_data[2]['selector'] = '.dropdown_mute_option'
        response_data[2]['HTML_snippet'] = mark_safe('<span class="glyphicon glyphicon-ban-circle"></span>Mute all activity')
    else:
        response_data = [{},{}]
        response_data[0]['selector'] = '.follow_button'
        response_data[0]['HTML_snippet'] = 'Follow'
        response_data[1]['selector'] = '.dropdown_follow_option'
        response_data[1]['HTML_snippet'] = 'Follow'
    return response_data

# 3. Put together the AJAX response data for when the previous page has a follow option in a dropdown header, such as on the user gallery page.
# Input: request_user, uploader_user, username of the uploader. Output: response_data
def get_follow_option_in_dropdown_header_response(request_user, uploader_user, username):
    response_data = [{}]
    response_data[0]['selector'] = '.header_follow_button'
    if request_user.user_profile in uploader_user.user_profile.followers.all():
        response_data[0]['HTML_snippet'] = 'Unfollow <div class="default-font inline-block">@' + username + " (" + str(uploader_user.user_profile.followers.count()) + ")</div>"
    else:
        response_data[0]['HTML_snippet'] = 'Follow <div class="default-font inline-block">@' + username + " (" + str(uploader_user.user_profile.followers.count()) + ")</div>" 
    return response_data
