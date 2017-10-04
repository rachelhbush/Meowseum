# Description: Process a request from a moderator to delete a comment.

from Meowseum.models import Upload, Comment
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
import json
from Meowseum.views.slide_page import get_comments_from_unmuted_users

# 0. Main function.
def page(request, comment_id):
    if request.is_ajax():
        if request.user.has_perm('Meowseum.delete_comment'):
            upload = delete_comment(request, comment_id)
            return get_server_response(request, comment_id, upload)
        else:
            return HttpResponse(status=403)
    else:
        if request.user.has_perm('Meowseum.delete_comment'):
            delete_comment(request, comment)
            return HttpResponseRedirect( reverse('slide_page', args=[comment.upload.relative_url]))
        else:
            # The user visited by navigation bar for some reason and shouldn't be here. Return a 403.
            return HttpResponse(status=403)

# 1. Delete the comment.
# Input: request, comment_id. Output: upload, the upload record associated with the comment.
def delete_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    upload = comment.upload
    if not comment.commenter.is_staff or comment.commenter == request.user:
        # Comment deletion is only allowed when the page-requesting user is a moderator and the commenter isn't a moderator,
        # or the moderator is deleting his or her own comment.
        comment.delete()
    return upload

# 2. Put together the AJAX response for when the server has successfully processed the form.
# Input: request, comment_id. Output: An HTTP response containing a JSON object to be sent back to AJAX.
def get_server_response(request, comment_id, upload):
    comments_from_unmuted_users = get_comments_from_unmuted_users(request, upload)
    response_data = [{}]
    
    if comments_from_unmuted_users.count() > 0:
        response_data[0]['selector'] = '.comment[action*="/' + comment_id + '/"]'
    else:
        response_data[0]['selector'] = '#posted-comments'    
    response_data[0]['method'] = 'remove'
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")
