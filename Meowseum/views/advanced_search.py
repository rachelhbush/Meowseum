# Description: This is the form where a user can perform a search using a GUI instead of a single search field.
# If the form doesn't have errors, then the view redirects the user to a search gallery page.

from Meowseum.forms import AdvancedSearchForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import increment_hit_count

def page(request):
    if request.GET:
        form = AdvancedSearchForm(request.GET)
        if form.is_valid():
            # Retrieve the query string for the search. It will have the parameters listed in the same order as in the HTML, which
            # will make the URL more readable than other ways of retrieving the query string.
            query_string = request.META['QUERY_STRING']
            # Redirect to the search page, where the querying will be done using the query string.
            return HttpResponseRedirect(reverse('search')+"?"+query_string)
        else:
            return render(request, 'en/public/advanced_search.html', {'form':form})
    else:
        increment_hit_count(request, "advanced_search")
        form = AdvancedSearchForm()
        return render(request, 'en/public/advanced_search.html', {'form':form})
