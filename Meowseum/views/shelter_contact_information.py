# Description: This is the form for registering as a shelter and editing the information on file.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from Meowseum.models import Shelter
from Meowseum.forms import ShelterForm, AddressForm

@login_required
# 0. Main function.
def page(request):
    main_form, profile_address_form, mailing_address_form, user_has_shelter_record_on_file = get_forms_and_shelter_status(request)
    if all([main_form.is_valid(), profile_address_form.is_valid(), mailing_address_form.is_valid()]):
        process_forms(request, main_form, profile_address_form, mailing_address_form)
        return redirect('index')
    else:
        return render(request, 'en/public/shelter_contact_information.html', {'main_form': main_form,
                                                                              'profile_address_form': profile_address_form,
                                                                              'mailing_address_form': mailing_address_form,
                                                                              'user_has_shelter_record_on_file':user_has_shelter_record_on_file})

# 1. Construct the forms, using previously provided information if available. Determine the user_has_shelter_record_on_file variable, whether or not
# the shelter has a record on file yet will be passed to the template. The extra "Save changes" button in the middle of the form needs to be hidden,
# because if the user clicked it before finishing the form, there would be a lot of "This field is required" error messages.
# Input: request.
# Output: main_form, profile_address_form, mailing_address_form, and user_has_shelter_record_on_file, a boolean value.
def get_forms_and_shelter_status(request):
    try:
        shelter = Shelter.objects.get(account = request.user)
        main_form = ShelterForm(request.POST or None, instance=shelter)
        profile_address_form = AddressForm(request.POST or None, instance=shelter.profile_address, required=('city', 'state_or_province', 'country', 'zip_code') )
        mailing_address_form = AddressForm(request.POST or None, instance=shelter.mailing_address, required='__all__')
        user_has_shelter_record_on_file = True
    except Shelter.DoesNotExist:
        main_form = ShelterForm(request.POST or None)
        profile_address_form = AddressForm(request.POST or None, required=('city', 'state_or_province', 'country', 'zip_code') )
        mailing_address_form = AddressForm(request.POST or None, required='__all__')
        user_has_shelter_record_on_file = False
    return main_form, profile_address_form, mailing_address_form, user_has_shelter_record_on_file

# 2. Input: request, main_form, profile_address_form, mailing_address_form.
# Output: None.
def process_forms(request, main_form, profile_address_form, mailing_address_form):
    shelter = main_form.save(commit=False)
    shelter.account = request.user
    shelter.profile_address = profile_address_form.save()
    shelter.mailing_address = mailing_address_form.save()
    shelter.save()
