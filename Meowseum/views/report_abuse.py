# Description: This is the form where a user files an abuse report about a user or post.

from Meowseum.models import AbuseReport
from django.contrib.auth.models import User
from Meowseum.forms import AbuseReportForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import increment_hit_count

def page(request):
    template_variables = {}
    if request.POST:
        form = AbuseReportForm(request.POST)
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
            template_variables['form'] = form
            return render(request, 'en/public/report_abuse.html', template_variables)
    else:
        increment_hit_count(request, "report_abuse")
        offending_username = request.GET.get('offending_username')
        referral_url = request.GET.get('referral_url')
        if offending_username == None or referral_url == None:
            template_variables['form'] = AbuseReportForm()
        else:
            template_variables['form'] = AbuseReportForm(initial={'offending_username': offending_username,
                                                              'url':'http://www.Meowseum.com/'+referral_url})
        
        return render(request, 'en/public/report_abuse.html', template_variables)
