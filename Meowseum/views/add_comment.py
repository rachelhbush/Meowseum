# Description: Process a request from a user to add a new comment.

from Meowseum.models import Upload, Comment
from Meowseum.forms import CommentForm
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
import json

# 0. Main function.
def page(request, relative_url):
    if request.user.is_authenticated():
        try:
            # Retrieve the appropriate slide for the URL.
            upload = Upload.objects.get(relative_url=relative_url)
        except ObjectDoesNotExist:
            # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
            return HttpResponseRedirect(request, reverse('index'))

        # Set up the form where the user can comment on the slide.
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            save_comment_form(upload, comment_form, request.user)
            return HttpResponseRedirect( reverse('slide_page', args=[relative_url])) 
        else:
            # The form has errors, but there isn't any way to return errors to the original view without using a querystring,
            # and implementing this is a lower priority than getting the form working with AJAX.
            return HttpResponseRedirect( reverse('slide_page', args=[relative_url]))    
    else:
        return HttpResponseRedirect(reverse('login') + "?next=" + reverse('slide_page', args=[relative_url]))

# 1. Save the comment form.
# Input: upload, comment_form. Output: None.
def save_comment_form(upload, comment_form, request_user):
    new_comment_record = comment_form.save(commit=False)
    new_comment_record.commenter = request_user
    new_comment_record.upload = upload
    new_comment_record.save()
