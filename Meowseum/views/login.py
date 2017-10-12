# Description: Login form. This is the view for the login page. It uses an "email or username" field. One of the first people to leave feedback wrote to me "I can't
# log in. It wants my email address", even though he gave it when he signed up. This kind of field is unconventional, but hopefully it will lower
# barriers to logging in.

from django import forms
from django.contrib.auth.models import User
from Meowseum.forms import LoginForm
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.shortcuts import render, redirect
from Meowseum.common_view_functions import increment_hit_count

def page(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
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
                return redirect(request.GET['next'])
            else:
                # If the user came across the login page by navigating to it, then redirect to the front page.
                return redirect('index')
    else:
        if request.method == 'GET':
            increment_hit_count(request, "login")
        return render(request, 'en/public/login.html', {'form' : form})
