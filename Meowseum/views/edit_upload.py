# Description: Edit an upload. In order to only use one URL, this view applies to uploads in all categories.
# At first, this will only affect the fields for Adoption, Lost, and Found.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from Meowseum.common_view_functions import redirect
from django.core.exceptions import PermissionDenied
from Meowseum.models import Upload, Adoption, Lost, Found
from Meowseum.forms import EditUploadForm, AdoptionForm, BondedWithForm, LostForm, FoundForm

@login_required
# 0. Main function.
def page(request, relative_url):
    upload = get_object_or_404(Upload, relative_url=relative_url)
    if request.user != upload.uploader:
        # Make sure only the author of the upload can edit it.
        raise PermissionDenied
    
    # Define the heading that will be used in the form's header.
    heading = 'Editing "'+ upload.title + '"'
    upload_category = upload.get_category()
    if upload_category == 'adoption':
        return render_adoption_editing_view(request, upload, heading)
    elif upload_category == 'lost':
        return render_lost_editing_view(request, upload, heading)
    elif upload_category == 'found':
        return render_found_editing_view(request, upload, heading)
    else:
        return render_pet_editing_view(request, upload, heading)

# 1. Render a form for editing an upload in the Adoption category.
def render_adoption_editing_view(request, upload, heading):
    main_form = AdoptionForm(request.POST or None, instance=upload.adoption)
    bonded_with_form = BondedWithForm(request.POST or None, initial=initialize_bonded_with_form(upload))
    edit_upload_form = EditUploadForm(request.POST or None, instance=upload)
    if all([main_form.is_valid(), bonded_with_form.is_valid(), edit_upload_form.is_valid()]):
        adoption_record = main_form.save(commit=False)
        adoption_record.internal_id = bonded_with_form.cleaned_data["internal_id"]
        adoption_record.save()
        edit_bonded_with_information(adoption_record, bonded_with_form.cleaned_data["bonded_with_IDs"])
        edit_upload_form.save()
        return redirect('index')
    else:
        return render(request, 'en/public/edit_upload.html', \
                      {'upload_category': 'adoption', 'main_form':main_form, 'bonded_with_form':bonded_with_form, 'edit_upload_form':edit_upload_form, 'heading':heading, 'upload': upload})

# 2. Render a form for editing an upload in the Lost category.
def render_lost_editing_view(request, upload, heading):
    main_form = LostForm(request.POST or None, instance=upload.lost)
    edit_upload_form = EditUploadForm(request.POST or None, instance=upload)
    if all([main_form.is_valid(), edit_upload_form.is_valid()]):
        main_form.save()
        edit_upload_form.save()
        return redirect('index')
    else:
        # The upload record is being passed as context in order to use it to know whether to show or hide the nested form for describing any collar or microchip the pet may have.
        return render(request, 'en/public/edit_upload.html', \
                      {'upload_category': 'lost', 'main_form':main_form, 'edit_upload_form':edit_upload_form, 'heading':heading, 'upload': upload})
        
# 3. Render a form for editing an upload in the Found category.
def render_found_editing_view(request, upload, heading):
    main_form = FoundForm(request.POST or None, instance=upload.found)
    edit_upload_form = EditUploadForm(request.POST or None, instance=upload)
    if all([main_form.is_valid(), edit_upload_form.is_valid()]):
        main_form.save()
        edit_upload_form.save()
        return redirect('index')
    else:
        return render(request, 'en/public/edit_upload.html', \
                      {'upload_category': 'found', 'main_form':main_form, 'edit_upload_form':edit_upload_form, 'heading':heading, 'upload': upload})

# 4. Render a form for editing an upload in the Pets category.
def render_pet_editing_view(request, upload, heading):
    edit_upload_form = EditUploadForm(request.POST or None, instance=upload)
    if edit_upload_form.is_valid():
        edit_upload_form.save()
        return redirect('index')
    else:
        return render(request, 'en/public/edit_upload.html', {'upload_category': 'pets', 'edit_upload_form':edit_upload_form, 'heading':heading, 'upload': upload})

# 1.1. Input: upload, an Upload record.
# Output: A dictionary containing the values with which the BondedWithForm should be initialized.
def initialize_bonded_with_form(upload):
    list_of_IDs = []
    for record in upload.adoption.bonded_with.all():
        list_of_IDs = list_of_IDs + [record.internal_id]
    bonded_with_IDs = ', '.join(list_of_IDs)
    return {'bonded_with_IDs': bonded_with_IDs, 'internal_id': upload.adoption.internal_id}

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
