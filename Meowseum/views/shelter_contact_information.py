# Description: This is the form for registering as a shelter and editing the information on file.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from Meowseum.models import Shelter
from Meowseum.forms import ShelterForm

@login_required
def page(request):
    # Whether or not the shelter has a record on file yet will be passed to the template. The extra "Save changes" button in the middle of the form
    # needs to be hidden, because if the user clicked it before finishing the form, there would be a lot of "This field is required" error messages.
    user_has_shelter_record_on_file = True
    try:
        shelter = Shelter.objects.get(account = request.user)
        form = ShelterForm(request.POST or None, instance=shelter)
    except Shelter.DoesNotExist:
        user_has_shelter_record_on_file = False
        form = ShelterForm(request.POST or None)
            
    if form.is_valid():
        shelter = form.save(commit=False)
        shelter.account = request.user
        shelter.save()
        return redirect('index')
    else:
        return render(request, 'en/public/shelter_contact_information.html', {'form':form, 'user_has_shelter_record_on_file':user_has_shelter_record_on_file})
