# Description: Like or unlike action. This is the page for processing a request from a slide page's Like button, using the URL "slide/relative_url/like".
# Currently, this is only for AJAX requests, but it is designed to handle requests when JavaScript is disabled.

from Meowseum.models import Upload, Like
from Meowseum.common_view_functions import redirect, ajaxWholePageRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

# 0. Main function.
def page(request, relative_url):    
    if request.user.is_authenticated():
        upload = get_object_or_404(Upload, relative_url=relative_url)
        like_or_unlike(upload, request.user)
        if request.is_ajax():
            # If the request is AJAX, then knowing the request is successful, the Like count can be incremented or decremented client-side, rather than calculating it again.
            # So, nothing further needs to be done, except returning the required HTTPResponse.
            return HttpResponse()
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the slide page to update it.
            return redirect('slide_page', args=[relative_url])
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the slide page after the user logs in.
        return ajaxWholePageRedirect(request, 'login', GET_args = "?next=" + reverse('slide_page', args=[relative_url]))

# 1. Update the database to show the user has liked or has unliked the upload.
# Input: upload. request_user, a record for the User making the request. Output: None.
def like_or_unlike(upload, request_user):
    try:
        # Try to obtain a Like record for this upload by this user.
        like_record = Like.objects.get(upload=upload, liker=request_user)
        # If there is a matching Like record, delete it.
        like_record.delete()
    except Like.DoesNotExist:
        # If there isn't a matching Like record, create it.
        like_record = Like(upload=upload, liker=request_user)
        like_record.save()
