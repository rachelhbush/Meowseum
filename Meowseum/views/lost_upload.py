# Description: This form is for all of the fields in the upload process relating to the Lost category.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from Meowseum.models import Upload, Lost
from Meowseum.forms import LostForm, VerifyDescriptionForm

@login_required
def page(request):
    # Obtain the logged-in user's most recent file submission. If the user hasn't submitted a file yet, then redirect to the homepage.
    try:
        upload = Upload.objects.filter(uploader=request.user).order_by("-id")[0]
    except IndexError:
        # If the user hasn't submitted a file yet, then the user shouldn't be here.
        raise PermissionDenied
    # Define the heading that will be used in the form's header.
    heading = "Uploading "+ upload.metadata.original_file_name + upload.metadata.original_extension
    
    lost_form = LostForm(request.POST or None)
    verify_description_form = VerifyDescriptionForm(request.POST or None, initial={'description':upload.description})
    if lost_form.is_valid() and verify_description_form.is_valid():
        new_lost_record = lost_form.save(commit=False)
        new_lost_record.upload = upload
        new_lost_record.save()
        upload.description = verify_description_form.cleaned_data['description']
        upload.save()
        return redirect('index')
    else:
        return render(request, 'en/public/lost_upload.html', {'lost_form':lost_form, 'verify_description_form':verify_description_form, 'heading':heading})
