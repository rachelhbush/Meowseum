# Description: This is the form where a user files an abuse report about a user or post.

from Meowseum.models import AbuseReport
from django.contrib.auth.models import User
from Meowseum.forms import AbuseReportForm
from django.shortcuts import render
from Meowseum.common_view_functions import redirect, increment_hit_count
from Meowseum.context_processors import constant_variables

# 0. Main function
def page(request):
    form = AbuseReportForm(request.POST or None, initial=get_initial_data_from_querystring(request))   
    if form.is_valid():
        offending_user = User.objects.get(username=form.cleaned_data['offending_username'])
        new_record = AbuseReport(offending_user=offending_user,
                                 abuse_type=form.cleaned_data['abuse_type'],
                                 abuse_description=form.cleaned_data['abuse_description'],
                                 url=form.cleaned_data['url'])
        if request.user.is_authenticated:
            new_record.filer = request.user
        new_record.save()
        return redirect('index')
    else:
        if request.method == 'GET':
            increment_hit_count(request, "report_abuse")
        return render(request, 'en/public/report_abuse.html', {'form': form})

# 1. Automatically fill in two of the fields based on the page from which the user is visiting.
# Input: request.
# Output: initial_data, a dictionary.
def get_initial_data_from_querystring(request):
    initial_data = {}
    try:
        initial_data['offending_username'] = request.GET['offending_username']
    except KeyError:
        initial_data['offending_username'] = ''
    try:
        # The referral URL is relative to the website domain name, but the URL validator will only validate a full URL, so prefix the site domain name.
        domain_name = constant_variables(request)['domain_name']
        initial_data['url'] = 'https://www.' + domain_name + request.GET['referral_url']
    except KeyError:
        initial_data['url'] = ''
    return initial_data
