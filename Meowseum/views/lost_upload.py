# lost_upload_v0_0_0_7.py by Rachel Bush. Date finished: 
# PROGRAM ID: lost_upload.py (_v0_0_0_7) / Lost section of the upload process
# INSTALLATION: Python 3.5, Django 1.9.2
# REMARKS: This form is for all of the fields relating to the Lost category.
# VERSION REMARKS: 

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import Upload, Lost
from Meowseum.forms import LostForm, VerifyDescriptionForm
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
        form = LostForm(request.POST)
        verify_description_form = VerifyDescriptionForm(request.POST)
        if form.is_valid() and verify_description_form.is_valid():
            new_lost_record = form.save(commit=False)
            new_lost_record.upload = upload
            new_lost_record.save()
            upload.description = verify_description_form.cleaned_data['description']
            upload.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'en/public/lost_upload.html', {'form':form, 'verify_description_form':verify_description_form, 'upload_record':upload, 'heading':heading})
    else:
        form = LostForm()
        verify_description_form = VerifyDescriptionForm(initial={"description":upload.description})
        return render(request, 'en/public/lost_upload.html', {'form':form, 'verify_description_form':verify_description_form, 'upload_record':upload, 'heading':heading})
