# Description: This is the page for processing a request to subscribe to a tag, either via a dropdown option in the header or via the URL bar.

from Meowseum.models import Tag
from Meowseum.common_view_functions import redirect, ajaxWholePageRedirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import json

def page(request, tag_name):
    if request.user.is_authenticated:
        tag = get_object_or_404(Tag, name=tag_name.lower())
        
        if tag in request.user.user_profile.subscribed_tags.all():
            request.user.user_profile.subscribed_tags.remove(tag) # Unsubscribe
        else:
            request.user.user_profile.subscribed_tags.add(tag) # Subscribe

        if request.is_ajax():
            response_data = [{}]
            response_data[0]['selector'] = '.header_subscribe_button'
            # Having already changed the Subscribe status, the if suites are now reversed.
            if tag in request.user.user_profile.subscribed_tags.all():
                response_data[0]['HTML_snippet'] = mark_safe('Unsubscribe from <div class="default-font inline-block">#' + tag_name +  ' (' + str(tag.subscribers.count()) + ')</span></div>')
            else:
                response_data[0]['HTML_snippet'] = mark_safe('Subscribe to <div class="default-font inline-block">#' + tag_name + ' (' + str(tag.subscribers.count()) + ')</span></div>')
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # If the request isn't AJAX (JavaScript is disabled), redirect back to the previous page.
            return redirect('tag_gallery', tag_name.lower())
    else:
        # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
        # Redirect the user back to the previous page after the user logs in.
        return ajaxWholePageRedirect(request, 'login', query = 'next=' + reverse('tag_gallery', args=[tag_name.lower()]))
