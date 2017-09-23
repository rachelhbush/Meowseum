from django.contrib.auth.decorators import login_required
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from django.db.models import Sum
from django.shortcuts import render

@login_required
def page(request):
    if not request.user.is_staff:
        # Make the page accessible only to the site administrator.
        return HttpResponseRedirect(reverse('index'))
    sitewide_hit_count = HitCount.objects.all().aggregate(sitewide_hit_count=Sum('hits'))['sitewide_hit_count']
    return render(request, 'en/private/site_statistics.html', {'sitewide_hit_count':sitewide_hit_count})
