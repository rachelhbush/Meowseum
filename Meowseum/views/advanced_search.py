# Description: This is the form where a user can perform a search using a GUI instead of a single search field.
# If the form doesn't have errors, then the view redirects the user to a search gallery page.

from Meowseum.forms import AdvancedSearchForm
from django.shortcuts import render
from Meowseum.common_view_functions import redirect, get_ordered_querystring_from_form, increment_hit_count

def page(request):
    form = AdvancedSearchForm(request.GET or None)
    if form.is_valid():
        ordered_querystring = get_ordered_querystring_from_form(form, excluding_blank_fields=True)        
        # Redirect to the search page, where the querying will be done.
        return redirect('search', query = ordered_querystring)
    else:
        if str(request.GET) == '<QueryDict: {}>':
            increment_hit_count(request, "advanced_search")
    return render(request, 'en/public/advanced_search.html', {'form':form})
