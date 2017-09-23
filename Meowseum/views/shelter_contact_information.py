# shelter_contact_information_v0_0_3.py by Rachel Bush. Date finished: 2/24/2017 10:18 PM
# PROGRAM ID: shelter_contact_information.py (_v0_0_3) / Shelter contact information
# INSTALLATION: Python 3.5, Django 1.9.2
# REMARKS: This is the form for registering as a shelter and editing the information on file.
# VERSION REMARKS: 1. I refactored the view using a simpler pattern, because I learned how to make a ModelForm's .save() method update a form, and I learned that
# form constructors will accept "or None". 1/6/2017 9:06AM 2. I added the login decorator to prevent an exception from the user being logged out.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import Shelter
from Meowseum.forms import ShelterForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

@login_required
def page(request):
    # Whether or not the shelter has a record on file yet will be passed to the template. The extra "Save changes" button in the middle of the form
    # needs to be hidden, because if the user clicked it before finishing the form, there would be a lot of "This field is required" error messages.
    user_has_shelter_record_on_file = True
    try:
        shelter = Shelter.objects.get(account = request.user)
        form = ShelterForm(request.POST or None, instance=shelter)
    except ObjectDoesNotExist:
        user_has_shelter_record_on_file = False
        form = ShelterForm(request.POST or None)
            
    if form.is_valid():
        shelter = form.save(commit=False)
        shelter.account = request.user
        shelter.save()
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'en/public/shelter_contact_information.html', {'form':form, 'user_has_shelter_record_on_file':user_has_shelter_record_on_file})
