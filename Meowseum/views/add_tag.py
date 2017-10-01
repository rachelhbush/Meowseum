# Description: Process a request to add a new tag to the slide page. The request must be POST, meaning the user should
# have been sent from the slide page.

from Meowseum.models import Upload, Tag
from Meowseum.forms import TagForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

# 0. Main function.
def page(request, relative_url):
    if request.user.is_authenticated():
        # Set up the form where any user can add a new tag to the slide.
        tag_form = TagForm(request.POST)
        if tag_form.is_valid():
            try:
                # Retrieve the appropriate slide for the URL.
                upload = Upload.objects.get(relative_url=relative_url)
            except ObjectDoesNotExist:
                # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
                return HttpResponseRedirect(reverse('index'))
            
            name = tag_form.cleaned_data['name'].lstrip("#").lower()
            try:
                # If the tag does exist, then associate this upload record with it.
                existing_tag = Tag.objects.get(name=name)
                existing_tag.uploads.add(upload)
                existing_tag.save()
            except ObjectDoesNotExist:
                # If the tag doesn't exist, create a new one and add the most recent upload as the first record.
                new_tag = Tag(name=name)
                new_tag.save()
                new_tag.uploads.add(upload)
                new_tag.save()
            return HttpResponseRedirect( reverse('slide_page', args=[relative_url]))
        else:
            # The form has errors, but there isn't any way to return errors to the original view without using a querystring,
            # and implementing this is a lower priority than getting the form working with AJAX.
            return HttpResponseRedirect( reverse('slide_page', args=[relative_url]))
    else:
        return HttpResponseRedirect(reverse('login') + "?next=" + reverse('slide_page', args=[relative_url]))
