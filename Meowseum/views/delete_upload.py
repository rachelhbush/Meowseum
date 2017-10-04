# Description: This is the page for processing a request to delete the upload. The request can be from the uploader or from a moderator.

from Meowseum.models import Upload
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
import json

def page(request, relative_url):    
    if request.user.is_authenticated():
        try:
            # Retrieve the appropriate slide for the URL.
            upload = Upload.objects.get(relative_url=relative_url)
        except ObjectDoesNotExist:
            # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
            return HttpResponseRedirect(reverse('index'))
        uploader = upload.uploader.user_profile
        viewer = request.user.user_profile
        response_data = [{}]

        if viewer == uploader or (request.user.has_perm('Meowseum.delete_upload') and not upload.uploader.is_staff):
            upload.delete()
            # After deletion, the user needs to immediately be redirected to another page, or else exceptions from expecting the upload such as
            # '"<Upload: Piper the Turkish Van cat>" needs to have a value for field "upload" before this many-to-many relationship can be used.' will occur.
            # If deletion didn't happen because the user accessed the page, via the URL bar,for an upload without user permissions, then there still
            # needs to be a redirect because Django requires returning an HTTPResponse.
            return ajaxWholePageRedirect(request, reverse('index'))
        elif viewer != uploader and (request.user.has_perm('Meowseum.delete_upload') and upload.uploader.is_staff):
            response_data[0]['selector'] = '.dropdown_delete_option'
            response_data[0]['HTML_snippet'] = """<span class="glyphicon glyphicon-remove-circle"></span><div class="inline-block">You can't delete an upload from another moderator.<br>Please contact an administrator!</div>"""
        else:
            # A regular user accessed the page, probably via the URL bar, for an upload without user permissions. Return a 403 error.
            return HttpResponseForbidden()
    
        if request.is_ajax():
            # The request is AJAX when using the Follow button dropdown to moderate, in order to relay the error when the upload is from a moderator.
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # The request is a regular GET request when the user visits via the Delete button (link) on one of the user's uploads. The URL bar also works.
            # Redirect to the front page after processing.
            return HttpResponseRedirect(reverse('index'))
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the slide page after the user logs in.
        return ajaxWholePageRedirect(request, reverse('login')+ "?next=" + urlencode(reverse('slide_page', args=[relative_url])))
