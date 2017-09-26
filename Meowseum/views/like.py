# Description: Like or unlike action. This is the page for processing a request from a slide page's Like button, using the URL "slide/relative_url/like".
# Currently, this is only for AJAX requests, but it is designed to handle requests when JavaScript is disabled.

from Meowseum.models import Upload, Like
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import urlencode

def page(request, relative_url):    
    if request.user.is_authenticated():
        try:
            # Retrieve the appropriate slide for the URL.
            upload = Upload.objects.get(relative_url=relative_url)
        except ObjectDoesNotExist:
            # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
            return HttpResponseRedirect(reverse('index'))
         
        try:
            # Try to obtain a Like record for this upload by this user.
            like_record = Like.objects.get(upload=upload, liker=request.user)
            # If there is a matching Like record, delete it.
            like_record.delete()
        except ObjectDoesNotExist:
            # If there isn't a matching Like record, create it.
            like_record = Like(upload=upload, liker=request.user)
            like_record.save()

        if request.is_ajax():
            # If the request is AJAX, then knowing the request is successful, the Like count can be incremented or decremented client-side, rather than calculating it again.
            # So, nothing further needs to be done, except returning the required HTTPResponse.
            return HttpResponse()
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the slide page to update it.
            return HttpResponseRedirect( reverse('slide_page', args=[relative_url]) )
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the slide page after the user logs in.
        return ajaxWholePageRedirect(request, reverse('login') + "?next=" + urlencode(reverse('slide_page', args=[relative_url])))
