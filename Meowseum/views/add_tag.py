# Description: Process a request to add a new tag to the slide page. The request must be POST, meaning the user should
# have been sent from the slide page.

from Meowseum.models import Upload, Tag
from Meowseum.forms import TagForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import json

# 0. Main function.
def page(request, relative_url):
    upload = get_object_or_404(Upload, relative_url=relative_url)
    
    if request.is_ajax():
        if request.user.is_authenticated():
            tag_form = TagForm(request.POST or None)
            if tag_form.is_valid():
                process_tag_form(upload, relative_url, tag_form)
                return get_successful_submission_response(request, upload, relative_url)
            else:
                return get_response_to_erroneous_data(request, upload, relative_url, tag_form)
        else:
            # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
            # Redirect the user back to the previous page after the user logs in.
            return ajaxWholePageRedirect(request, 'login', GET_args = "?next=" + reverse('slide_page', args=[relative_url]))
    else:
        if request.user.is_authenticated():
            tag_form = TagForm(request.POST or None)
            if tag_form.is_valid():
                process_tag_form(upload, relative_url, tag_form)
                return redirect('slide_page', args=[relative_url])
            else:
                # The form has errors, but there isn't any way to return errors to the original view without using a querystring,
                # and implementing this is a lower priority than getting the form working with AJAX.
                return redirect('slide_page', args=[relative_url])
        else:
            return redirect('login', GET_args = "?next=" + reverse('slide_page', args=[relative_url]))

# 1. Input: upload, relative_url, tag_form. Output: None.
def process_tag_form(upload, relative_url, tag_form):
    tag_name = tag_form.cleaned_data['name'].lstrip("#").lower()
    try:
        # If the tag does exist, then associate this upload record with it.
        existing_tag = Tag.objects.get(name=tag_name)
        existing_tag.uploads.add(upload)
        existing_tag.save()
    except Tag.DoesNotExist:
        # If the tag doesn't exist, create a new one and add the most recent upload as the first record.
        new_tag = Tag(name=tag_name)
        new_tag.save()
        new_tag.uploads.add(upload)
        new_tag.save()

# 2. Put together the AJAX response for when the server has successfully processed the form.
# Input: request, upload, relative_url, tag_form. Output: An HTTP response containing a JSON object to be sent back to AJAX.
def get_successful_submission_response(request, upload, relative_url):
    response_data = [{},{}]
    # The new HTML will replace the content of the <form> within the #tags section.
    response_data[0]['selector'] = '#tags > form'
    # After the form it successfully submitted, it will be reset to its original state.
    tag_form = TagForm()
    tags_form_HTTP_response = render(request, 'en/public/slide_page_tag_form.html', \
                                           {'upload':upload, 'relative_url': relative_url, 'tag_form': tag_form})
    # Convert the byte string content of the HTTP response to UTF-8 character encoding, then have Django recognize it as safe HTML
    # rather than an ordinary string.
    response_data[0]['HTML_snippet'] = mark_safe(tags_form_HTTP_response.content.decode('utf-8'))
    # Update the page with the new tag count.
    new_tag_count = upload.tags.count()
    response_data[1]['selector'] = '.tag-btn'
    response_data[1]['HTML_snippet'] = mark_safe('<span class="glyphicon glyphicon-tag"></span> ' + str(new_tag_count))
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# 3. Put together the AJAX response for when the user provided erroneous data.
# Input: request, upload, relative_url, tag_form. Output: An HTTP response containing a JSON object to be sent back to AJAX.
def get_response_to_erroneous_data(request, upload, relative_url, tag_form):
    response_data = [{}]
    # The new HTML will replace the content of the <form> within the #tags section.
    response_data[0]['selector'] = '#tags > form'
    tags_form_HTTP_response = render(request, 'en/public/slide_page_tag_form.html', \
                                           {'upload':upload, 'relative_url': relative_url, 'tag_form':tag_form})
    # Convert the byte string content of the HTTP response to UTF-8 character encoding, then have Django recognize it as safe HTML
    # rather than an ordinary string.
    response_data[0]['HTML_snippet'] = mark_safe(tags_form_HTTP_response.content.decode('utf-8'))
    return HttpResponse(json.dumps(response_data), content_type="application/json")
