# Description: This form allows the user to enter information that is required before they can post to the Adoption section (for fostering), the Lost section, or the Found section.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from Meowseum.models import UserContact
from Meowseum.forms import AddressForm, UserContactForm1, UserContactForm2

@login_required
def page(request):
    try:
        contact = UserContact.objects.get(account = request.user)
        main_form = UserContactForm1(request.POST or None, instance=contact)
        address_form = AddressForm(request.POST or None, required=('address_line_1', 'city', 'state_or_province', 'country', 'zip_code'), instance=contact.address)
    except UserContact.DoesNotExist:
        main_form = UserContactForm1(request.POST or None)
        address_form = AddressForm(request.POST or None, required=('address_line_1', 'city', 'state_or_province', 'country', 'zip_code'))
    user_form = UserContactForm2(request.POST or None, instance=request.user, required='__all__')

    if all([main_form.is_valid(), address_form.is_valid(), user_form.is_valid()]):
        contact = main_form.save(commit=False)
        contact.account = request.user
        contact.address = address_form.save()
        contact.save()
        user_form.save()
        return redirect('index')
    else:
        return render(request, 'en/public/user_contact_information.html', {'main_form':main_form, 'address_form':address_form, 'user_form':user_form})
