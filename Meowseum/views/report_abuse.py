# Description: This is the form where a user files an abuse report about a user or post.

from Meowseum.models import AbuseReport
from django.contrib.auth.models import User
from Meowseum.forms import AbuseReportForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import increment_hit_count

def page(request):
    template_variables, initial_data = {}, {}
    # Automatically fill in two of the fields based on the page from which the user is visiting.
    try:
        initial_data['offending_username'] = request.GET['offending_username']
    except:
        initial_data['offending_username'] = ''
    try:
        initial_data['url'] = 'http://www.meowseum.com' + request.GET['referral_url']
    except:
        initial_data['url'] = ''
    form = AbuseReportForm(request.POST or None, initial=initial_data)
    
    if form.is_valid():
        offending_user = User.objects.get(username=form.cleaned_data['offending_username'])
        if request.user.is_authenticated():
            filer = request.user
            new_record = AbuseReport(filer=filer,
                                     offending_user=offending_user,
                                     abuse_type=form.cleaned_data['abuse_type'],
                                     abuse_description=form.cleaned_data['abuse_description'],
                                     url=form.cleaned_data['url'])
        else:
            new_record = AbuseReport(offending_user=offending_user,
                                     abuse_type=form.cleaned_data['abuse_type'],
                                     abuse_description=form.cleaned_data['abuse_description'],
                                     url=form.cleaned_data['url'])
        new_record.save()
        return HttpResponseRedirect(reverse('index'))
    else:
        if request.method == 'GET':
            increment_hit_count(request, "report_abuse")
        template_variables['form'] = form
        return render(request, 'en/public/report_abuse.html', template_variables)
