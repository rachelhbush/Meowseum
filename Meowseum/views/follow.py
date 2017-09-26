# Description: Follow or unfollow action. This is the page for processing a request to a follow a user. The request will be from a slide page's Follow button or from a dropdown
# option on a user's gallery page.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
import json

def page(request, username):
    # The user can navigate to this page from the slide page, a user gallery page, the user profile page (in the future), or the URL bar. When
    # JavaScript is disabled, the two pages redirect to this page, and this page redirects back. When redirecting occurs, redirect to the user uploads gallery page
    # when the previous URL is unknown.
    previous_URL = urlencode(request.GET.get('next', reverse('gallery', args=[username])))
    if request.user.is_authenticated():
        try:
            uploader_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('index'))
        uploader = uploader_user.user_profile
        viewer = request.user.user_profile
        
        if viewer in uploader.followers.all():
            uploader.followers.remove(viewer)
        else:
            # In Meowseum's current system, muting silences all activity. A user cannot be muted and followed at the same time. When either status is added, the other needs to be removed.
            uploader.followers.add(viewer)
            uploader.muters.remove(viewer)
        uploader.save()

        if request.is_ajax():
            response_data = {}
            # The AJAX response will differ depending on the requesting page. Having already changed the Follow status, the if suites are now reversed.
            if '/slide/' in previous_URL or '/profile/' in previous_URL:
                # The response data will be inserted into the Follow button HTML.
                if viewer in uploader.followers.all():
                    response_data['.follow_button'] = mark_safe('<span class="default-content">Following</span><span class="rollover-content">Unfollow</span>')
                    response_data['.dropdown_follow_option'] = 'Unfollow'
                    response_data['.dropdown_mute_option'] = mark_safe('<span class="glyphicon glyphicon-ban-circle"></span>Mute all activity')
                else:
                    response_data['.follow_button'] = 'Follow'
                    response_data['.dropdown_follow_option'] = 'Follow'
            else:
                # The response data will be inserted into a header dropdown on a user's gallery page.
                if viewer in uploader.followers.all():
                    response_data['.header_follow_button'] = 'Unfollow <div class="default-font inline-block">@' + username + " (" + str(uploader.followers.count()) + ")</div>"
                else:
                    response_data['.header_follow_button'] = 'Follow <div class="default-font inline-block">@' + username + " (" + str(uploader.followers.count()) + ")</div>" 
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return HttpResponseRedirect(previous_URL)
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the previous page after the user logs in.
        return ajaxWholePageRedirect(request, reverse('login') + "?next=" + previous_URL)
