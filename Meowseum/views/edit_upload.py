# Description: Edit an upload. In order to only use one URL, this view applies to uploads in all categories.
# At first, this will only affect the fields for Adoption, Lost, and Found.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import Upload, Adoption, Lost, Found
from Meowseum.forms import AdoptionForm, BondedWithForm, LostForm, FoundForm, VerifyDescriptionForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

@login_required
# 0. Main function.
def page(request, relative_url):
    try:
        # Retrieve the appropriate slide for the URL.
        upload = Upload.objects.get(relative_url=relative_url)
    except ObjectDoesNotExist:
        # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
        return HttpResponseRedirect(reverse('index'))
    # Define the heading that will be used in the form's header.
    heading = 'Editing "'+ upload.title + '"'

    upload_category = upload.get_category()
    if upload_category == 'adoption':
        return render_adoption_editing_view(request, upload, heading)
# I'll program the other editing forms later.
##    elif upload_category == 'lost':
##        return render_lost_editing_view(request, upload, heading)
##    elif upload_category == 'found':
##        return render_found_editing_view(request, upload, heading)
##    else:
##        return render_pet_editing_view(request, upload, heading)

# 1. Render a form for editing an Adoption upload.
def render_adoption_editing_view(request, upload, heading):
    adoption_form = AdoptionForm(request.POST or None, instance=upload.adoption)
    bonded_with_form = BondedWithForm(request.POST or None, initial=initialize_bonded_with_information(upload))
    if adoption_form.is_valid() and bonded_with_form.is_valid():
        adoption_record = adoption_form.save()
        edit_bonded_with_information(adoption_record, bonded_with_form.cleaned_data["bonded_with_IDs"])
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'en/public/edit_upload.html', \
                      {'upload_category': 'adoption', 'adoption_form':adoption_form, 'bonded_with_form':bonded_with_form, 'upload':upload, 'heading':heading})

# 1.1. Input: upload, an Upload record.
# Output: A dictionary containing the values with which the BondedWithForm should be initialized.
def initialize_bonded_with_information(upload):
    list_of_IDs = []
    for record in upload.adoption.bonded_with.all():
        list_of_IDs = list_of_IDs + [record.internal_id]
    bonded_with_IDs = ', '.join(list_of_IDs)
    return {'bonded_with_IDs': bonded_with_IDs}

# 1.2. Update the association between the Adoption record and other Adoption records, using a comma-separated list of IDs.
# Input: adoption_record, bonded_with_IDs string. Output: None.
def edit_bonded_with_information(adoption_record, bonded_with_IDs):
    if bonded_with_IDs == '':
        adoption_record.bonded_with.clear()
    else:
        list_of_IDs = bonded_with_IDs.split(',')
        list_of_bonded_with_records = []
        for x in range(len(list_of_IDs)):
            list_of_IDs[x] = list_of_IDs[x].lstrip(' ')
            bonded_with_record = Adoption.objects.get(internal_id=list_of_IDs[x])
            list_of_bonded_with_records = list_of_bonded_with_records + [bonded_with_record]
        adoption_record.bonded_with.set(list_of_bonded_with_records)
