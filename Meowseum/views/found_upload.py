# found_upload_v0_0_0_6.py by Rachel Bush. Date last modified: 
# PROGRAM ID: found_upload.py (_v0_0_0_6) / Found section of the upload process
# INSTALLATION: Python 3.5, Django 1.9.2
# REMARKS: This form is for all of the fields relating to the Found category.
# VERSION REMARKS: 

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import Upload, Found
from Meowseum.forms import FoundForm, VerifyDescriptionForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

@login_required
def page(request):
    # Obtain the logged-in user's most recent file submission. If the user hasn't submitted a file yet, then redirect to the homepage.
    try:
        upload = Upload.objects.filter(uploader=request.user).order_by("-id")[0]
    except IndexError:
        return HttpResponseRedirect(reverse('index'))
    # Define the heading that will be used in the form's header.
    heading = "Uploading "+ upload.metadata.original_file_name + upload.metadata.original_extension
    
    if request.POST:
        form = FoundForm(request.POST)
        verify_description_form = VerifyDescriptionForm(request.POST)
        if form.is_valid() and verify_description_form.is_valid():
            new_found_record = form.save(commit=False)
            new_found_record.upload = upload
            new_found_record.save()
            upload.description = verify_description_form.cleaned_data['description']
            upload.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'en/public/found_upload.html', {'form':form, 'verify_description_form':verify_description_form, 'upload_record':upload, 'is_shelter':request.user.user_profile.is_shelter(), 'heading':heading})
    else:
        form = FoundForm()
        verify_description_form = VerifyDescriptionForm(initial={"description":upload.description})
        return render(request, 'en/public/found_upload.html', {'form':form, 'verify_description_form':verify_description_form, 'upload_record':upload, 'is_shelter':request.user.user_profile.is_shelter(), 'heading':heading})
