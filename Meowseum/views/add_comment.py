# Description: Process a request from a user to add a new comment.

from Meowseum.models import Upload, Comment
from Meowseum.forms import CommentForm
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
import json
from Meowseum.views.slide_page import get_comments_from_unmuted_users

# 0. Main function.
def page(request, relative_url):
    if request.is_ajax():
        if request.user.is_authenticated():
            try:
                # Retrieve the appropriate slide for the URL.
                upload = Upload.objects.get(relative_url=relative_url)
            except ObjectDoesNotExist:
                # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
                return ajaxWholePageRedirect(request, reverse('index'))

            comment_form = CommentForm(request.POST or None)
            if comment_form.is_valid():
                comment = save_comment_form(upload, comment_form, request.user)
                return get_successful_submission_response(request, comment)
            else:
                return get_response_to_erroneous_data(request, comment_form)
        else:
            # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
            # Redirect the user back to the previous page after the user logs in.
            return ajaxWholePageRedirect(request, reverse('login') + "?next=" + reverse('slide_page', args=[relative_url]))
    else:
        if request.user.is_authenticated():
            try:
                # Retrieve the appropriate slide for the URL.
                upload = Upload.objects.get(relative_url=relative_url)
            except ObjectDoesNotExist:
                # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
                return HttpResponseRedirect(request, reverse('index'))

            comment_form = CommentForm(request.POST or None)
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
# Input: upload, comment_form. Output: new_comment_record
def save_comment_form(upload, comment_form, request_user):
    new_comment_record = comment_form.save(commit=False)
    new_comment_record.commenter = request_user
    new_comment_record.upload = upload
    new_comment_record.save()
    return new_comment_record

# 2. Put together the AJAX response for when the server has successfully processed the form.
# Input: request, upload, relative_url, tag_form. Output: An HTTP response containing a JSON object to be sent back to AJAX.
def get_successful_submission_response(request, comment):
    response_data = [{},{}]
    # The new HTML will replace the content of the <form> within the #tags section.
    response_data[0]['selector'] = '#comments > form'
    # After the form it successfully submitted, it will be reset to its original state.
    comment_form = CommentForm()
    comment_form_HTML = render(request, 'en/public/slide_page_add_comment_form.html', {'comment_form': comment_form})
    # Convert the byte string content of the HTTP response to UTF-8 character encoding, then have Django recognize it as safe HTML
    # rather than an ordinary string.
    response_data[0]['HTML_snippet'] = mark_safe(comment_form_HTML.content.decode('utf-8'))

    if request.user.has_perm('Meowseum.delete_comment'):
        new_comment_section_HTML = render(request, 'en/public/slide_page_comment_with_delete_comment_button.html', {'comment': comment})
    else:
        new_comment_section_HTML = render(request, 'en/public/slide_page_comment_without_delete_comment_button.html', {'comment': comment})
    new_comment_section_HTML = mark_safe(new_comment_section_HTML.content.decode('utf-8'))
    comments_from_unmuted_users = get_comments_from_unmuted_users(request, comment.upload)
    if comments_from_unmuted_users.count() == 1:
        new_comment_section_HTML = '<div id="posted-comments">' + new_comment_section_HTML + '</div>'
        response_data[1]['selector'] = '#comments > form'
    else:
        response_data[1]['selector'] = '#comments .comment:last'
    response_data[1]['method'] = 'after'
    response_data[1]['HTML_snippet'] = new_comment_section_HTML
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# 3. Put together the AJAX response for when the user provided erroneous data.
# Input: request, upload, relative_url, tag_form. Output: An HTTP response containing a JSON object to be sent back to AJAX.
def get_response_to_erroneous_data(request, comment_form):
    response_data = [{}]
    # The new HTML will replace the content of the <form> within the #tags section.
    response_data[0]['selector'] = '#comments > form'
    comment_form_HTML = render(request, 'en/public/slide_page_add_comment_form.html', {'comment_form': comment_form})
    # Convert the byte string content of the HTTP response to UTF-8 character encoding, then have Django recognize it as safe HTML
    # rather than an ordinary string.
    response_data[0]['HTML_snippet'] = mark_safe(comment_form_HTML.content.decode('utf-8'))
    return HttpResponse(json.dumps(response_data), content_type="application/json")
