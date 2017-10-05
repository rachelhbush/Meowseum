# Description: This form is for all of the fields in the upload process relating to the Adoption category.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import Upload, Adoption
from Meowseum.forms import AdoptionForm, BondedWithForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

@login_required
# 0. Main function.
def page(request):
    # Obtain the logged-in user's most recent file submission. If the user hasn't submitted a file yet, then redirect to the homepage.
    try:
        upload = Upload.objects.filter(uploader=request.user).order_by("-id")[0]
    except IndexError:
        return HttpResponseRedirect(reverse('index'))
    # Define the heading that will be used in the form's header.
    heading = "Uploading "+ upload.metadata.original_file_name + upload.metadata.original_extension
    
    if request.POST:
        adoption_form = AdoptionForm(request.POST)
        bonded_with_form = BondedWithForm(request.POST)
        if adoption_form.is_valid() and bonded_with_form.is_valid():
            new_adoption_record = adoption_form.save(commit=False)
            new_adoption_record.upload = upload
            new_adoption_record.save()
            save_bonded_with_information(new_adoption_record, bonded_with_form.cleaned_data["bonded_with_IDs"])
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'en/public/adoption_upload.html', {'adoption_form':adoption_form, 'bonded_with_form':bonded_with_form, 'heading':heading})
    else:
        adoption_form = AdoptionForm()
        bonded_with_form = BondedWithForm()
        return render(request, 'en/public/adoption_upload.html', {'adoption_form':adoption_form, 'bonded_with_form':bonded_with_form, 'heading':heading})

# 1. If the "bonded_with_IDs" field was filled out, use its comma-separated list field to associate the new adoption record with a list of other adoption records.
# Input: new_adoption_record, bonded_with_IDs string. Output: None.
def save_bonded_with_information(new_adoption_record, bonded_with_IDs):
    if bonded_with_IDs != '':
        list_of_IDs = bonded_with_IDs.split(',')
        for x in range(len(list_of_IDs)):
            list_of_IDs[x] = list_of_IDs[x].lstrip(' ')
            bonded_with_record = Adoption.objects.get(internal_id=list_of_IDs[x])
            new_adoption_record.bonded_with.add(bonded_with_record)
        new_adoption_record.save()
