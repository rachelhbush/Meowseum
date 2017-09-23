# subscribe_v0_0_0_2.py by Rachel Bush. Last modified: 
# PROGRAM ID: subscribe.py (_v0_0_0_2) / Subscribe to a tag
# REMARKS: This is the page for processing a request to subscribe to a tag, either via a dropdown option in the header or via the URL bar.
# VERSION REMARKS: 

from Meowseum.models import Tag
from Meowseum.common_view_functions import ajaxWholePageRedirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
import json

def page(request, tag_name):
    template_variables = {}
    previous_URL = urlencode(reverse('tag_gallery', args=[tag_name.lower()]))
    if request.user.is_authenticated():
        try:
            tag = Tag.objects.get(name=tag_name.lower())
        except ObjectDoesNotExist:
            return HttpResponse(status=404)
        
        if tag in request.user.user_profile.subscribed_tags.all():
            request.user.user_profile.subscribed_tags.remove(tag) # Unsubscribe
        else:
            request.user.user_profile.subscribed_tags.add(tag) # Subscribe
        request.user.user_profile.save() 

        if request.is_ajax():
            response_data = {}
            # Having already changed the Subscribe status, the if suites are now reversed.
            if tag in request.user.user_profile.subscribed_tags.all():
                response_data['.header_subscribe_button'] = mark_safe('Unsubscribe from <div class="default-font inline-block">#' + tag_name +  ' (' +\
                                                                      str(tag.subscribers.count()) + ')</span></div>')
            else:
                response_data['.header_subscribe_button'] = mark_safe('Subscribe to <div class="default-font inline-block">#' + tag_name + ' (' +\
                                                                      str(tag.subscribers.count()) + ')</span></div>')
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return HttpResponseRedirect(previous_URL)
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the previous page after the user logs in.
        return ajaxWholePageRedirect(request, reverse('login') + "?next=" + previous_URL)
