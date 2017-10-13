# Description: Signup form. This is the page for signing up for an account on the website.

from django import forms
from django.contrib.auth.models import User
from Meowseum.models import UserProfile
from Meowseum.forms import SignupForm
from django.contrib.auth import authenticate, login
from django.utils import timezone
import string
import random
from django.shortcuts import render
from Meowseum.common_view_functions import redirect, increment_hit_count
from ipware.ip import get_real_ip

def page(request):
    form = SignupForm(request.POST or None)
    if form.is_valid():
        # Register.
        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        new_user = User.objects.create_user(username=username, email=email, password=password)
        new_user.is_active=True
        new_user.save()
        ip_address = get_real_ip(request)
        if ip_address is not None:
            new_profile = UserProfile(user_auth = new_user, registered_with_ip_address = get_real_ip(request))
        else:
            new_profile = UserProfile(user_auth = new_user)
        new_profile.save()
        # Log in as the newly registered user.
        user = authenticate(username=username, password=password)
        login(request, user)
        # Redirect to the front page.
        return redirect('index')
    else:
        if request.method == 'GET':
            increment_hit_count(request, "signup")
        return render(request, 'en/public/signup.html', {'form':form})
