# Description: This form is for all of the fields in the upload process relating to the Adoption category.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from django.core.exceptions import PermissionDenied
from Meowseum.models import Upload, Adoption
from Meowseum.forms import AdoptionForm

@login_required
# 0. Main function.
def page(request):
    # Obtain the logged-in user's most recent file submission.
    try:
        upload = Upload.objects.filter(uploader=request.user).order_by("-id")[0]
    except IndexError:
        # If the user hasn't submitted a file yet, then the user shouldn't be here.
        raise PermissionDenied
    # Define the heading that will be used in the form's header.
    heading = "Uploading "+ upload.metadata.original_file_name + upload.metadata.original_extension
    
    main_form = AdoptionForm(request.POST or None)
    if main_form.is_valid():
        new_adoption_record = main_form.save(commit=False)
        new_adoption_record.upload = upload
        new_adoption_record.save()
        add_bonded_with_information(new_adoption_record, main_form.cleaned_data["bonded_with_IDs"])
        return redirect('index')
    else:
        return render(request, 'en/public/adoption_upload.html', {'main_form':main_form, 'heading':heading})

# 1. If the "bonded_with_IDs" field was filled out, use its comma-separated list field to associate the new adoption record with a list of other adoption records.
# Input: new_adoption_record, bonded_with_IDs string. Output: None.
def add_bonded_with_information(new_adoption_record, bonded_with_IDs):
    if bonded_with_IDs != '':
        list_of_IDs = bonded_with_IDs.split(',')
        for x in range(len(list_of_IDs)):
            list_of_IDs[x] = list_of_IDs[x].lstrip(' ')
            bonded_with_record = Adoption.objects.get(internal_id=list_of_IDs[x])
            new_adoption_record.bonded_with.add(bonded_with_record)
