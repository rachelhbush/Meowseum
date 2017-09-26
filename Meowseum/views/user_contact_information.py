# Description: This form allows the user to enter information that is required before they can post to the Adoption section (for fostering), the Lost section, or the Found section.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.models import UserContact
from Meowseum.forms import UserContactForm1, UserContactForm2
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

@login_required
def page(request):
    try:
        contact = UserContact.objects.get(account = request.user)
        form1 = UserContactForm1(request.POST or None, instance=contact)
    except ObjectDoesNotExist:
        form1 = UserContactForm1(request.POST or None)
    form2 = UserContactForm2(request.POST or None, instance=request.user)
    
    if form1.is_valid() and form2.is_valid():
        contact = form1.save(commit=False)
        contact.account = request.user
        contact.save()
        form2.save()
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'en/public/user_contact_information.html', {'form1':form1, 'form2':form2})
