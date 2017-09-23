# login_v0_0_0_7.py by Rachel Bush. Date last modified: 
# PROGRAM ID: login.py (_v0_0_0_7) / Login form
# REMARKS: This is the view for the login page. It uses an "email or username" field. One of the first people to leave feedback wrote to me "I can't
# log in. It wants my email address", even though he gave it when he signed up. This kind of field is unconventional, but hopefully it will lower
# barriers to logging in.
# VERSION REMARKS: 

from django import forms
from django.contrib.auth.models import User
from Meowseum.forms import LoginForm
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import increment_hit_count

def page(request):
    if request.POST:
        # The user accessed the view by sending a POST request (form). Create a form object from the request data.
        form = LoginForm(request.POST)
        if form.is_valid():
            # Begin the login process.
            email_or_username = form.cleaned_data["email_or_username"]
            password = form.cleaned_data["password"]
            if '@' in email_or_username:
                username = User.objects.get(email=email_or_username).username
            else:
                username = email_or_username
            # Retrieve the User record.
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                user.user_profile.save()
                # If the user was redirected to the login page because the user was looking at a page restricted to logged in users, then redirect to the page the user had been trying to access.
                if request.GET.get('next') is not None:
                    return HttpResponseRedirect(request.GET['next'])
                else:
                    # If the user came across the login page by navigating to it, then redirect to the front page.
                    return HttpResponseRedirect(reverse('index'))
        else:
            # Return the form with error messages.
            return render(request, 'en/public/login.html', {'form' : form})
    else:
        increment_hit_count(request, "login")
        # The user accessed the view by navigating to a page that uses it. Load the page with a blank form.
        form = LoginForm()
        return render(request, 'en/public/login.html', {'form' : form})
