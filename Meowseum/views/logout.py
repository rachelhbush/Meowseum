from django.shortcuts import render
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def page(request):
  logout(request)
  # After logging out, redirect to the front page.
  return HttpResponseRedirect(reverse('index'))
