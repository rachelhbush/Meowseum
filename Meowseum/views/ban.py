# Description: This is the page for processing a request from a Follow button's Ban option.

from django.contrib.auth.models import User
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
import json

def page(request, username):
    # The moderator can navigate to this page from the slide page, the user page (in the future), or the URL bar. The first two pages redirect to this page with a querystring.
    # when JavaScript is disabled, then this page redirects back. When redirecting occurs, redirect to the user page when the previous URL is unknown.
    previous_URL = urlencode(request.GET.get('next', reverse('gallery', args=[username])))
    if request.user.is_authenticated() and request.user.has_perm('Meowseum.change_user'):
        # The user is a logged in moderator.
        try:
            uploader_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('index'))
        response_data = {}

        if uploader_user.is_active:
            if uploader_user.is_staff:
                response_data['.dropdown_ban_option'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span><div class="inline-block">You can't ban another moderator.<br>Please contact an administrator!</div>""")
            else:
                uploader_user.is_active = False
                uploader_user.save()
                response_data['.dropdown_ban_option'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span>Unban from Meowseum""")
        else:
            if uploader_user.is_staff:
                response_data['.dropdown_ban_option'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span><div class="inline-block">You can't unban another moderator.<br>Please contact an administrator!</div>""")
            else:
                uploader_user.is_active = True
                uploader_user.save()
                response_data['.dropdown_ban_option'] = mark_safe("""<span class="glyphicon glyphicon-exclamation-sign"></span>Ban from Meowseum""")

        if request.is_ajax():
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return HttpResponseRedirect(previous_URL)
    else:
        # The user shouldn't be here. Return a 403 error.
        return HttpResponseForbidden()
