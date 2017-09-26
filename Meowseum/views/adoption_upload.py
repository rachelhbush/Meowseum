# Description: This form is for all of the fields in the upload process relating to the Adoption category.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import Upload, Adoption
from Meowseum.forms import AdoptionForm
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
        form = AdoptionForm(request.POST)
        if form.is_valid():
            new_adoption_record = form.save(commit=False)
            new_adoption_record.upload = upload
            new_adoption_record.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'en/public/adoption_upload.html', {'form':form, 'upload_record':upload, 'heading':heading})
    else:
        form = AdoptionForm()
        return render(request, 'en/public/adoption_upload.html', {'form':form, 'upload_record':upload, 'heading':heading})

