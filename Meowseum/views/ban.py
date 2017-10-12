# Description: This is the page for processing a request from a Follow button's Ban option.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
import json

def page(request, username):
    # The moderator can navigate to this page from the slide page, the user page (in the future), or the URL bar. The first two pages redirect to this page with a querystring.
    # when JavaScript is disabled, then this page redirects back. When redirecting occurs, redirect to the user page when the previous URL is unknown.
    previous_URL = urlencode(request.GET.get('next', reverse('gallery', args=[username])))
    # Check whether the user is a logged in moderator.
    if request.user.is_authenticated() and request.user.has_perm('Meowseum.change_user'):
        uploader_user = get_object_or_404(User, username=username)
        
        response_data = [{}]
        response_data[0]['selector'] = '.dropdown_ban_option'
        if uploader_user.is_active:
            if uploader_user.is_staff:
                response_data[0]['HTML_snippet'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span><div class="inline-block">You can't ban another moderator.<br>Please contact an administrator!</div>""")
            else:
                uploader_user.is_active = False
                uploader_user.save()
                response_data[0]['HTML_snippet']  = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span>Unban from Meowseum""")
        else:
            if uploader_user.is_staff:
                response_data[0]['HTML_snippet'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span><div class="inline-block">You can't unban another moderator.<br>Please contact an administrator!</div>""")
            else:
                uploader_user.is_active = True
                uploader_user.save()
                response_data[0]['HTML_snippet'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span>Ban from Meowseum""")

        if request.is_ajax():
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return redirect(previous_URL)
    else:
        raise PermissionDenied
