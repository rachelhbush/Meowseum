# Description: Process a request from a moderator to delete a comment.

from Meowseum.models import Comment
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

# 0. Main function.
def page(request, comment_id):
    if request.user.has_perm('Meowseum.delete_comment'):
        comment = Comment.objects.get(id=comment_id)
        if not comment.commenter.is_staff or comment.commenter == request.user:
            # Comment deletion is only allowed when the page-requesting user is a moderator and the commenter isn't a moderator,
            # or the moderator is deleting his or her own comment.
            comment.delete()
        return HttpResponseRedirect( reverse('slide_page', args=[comment.upload.relative_url]))
    else:
        # The user visited by navigation bar for some reason and shouldn't be here. Redirect to the front page.
        return HttpResponseRedirect(reverse('index'))
