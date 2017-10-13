# Description: This is the form where a user can perform a search using a GUI instead of a single search field.
# If the form doesn't have errors, then the view redirects the user to a search gallery page.

from Meowseum.forms import AdvancedSearchForm
from django.shortcuts import render
from Meowseum.common_view_functions import redirect, increment_hit_count

def page(request):
    form = AdvancedSearchForm(request.GET or None)
    if form.is_valid():
        # Redirect to the search page, where the querying will be done.
        # The method this page uses for retrieving the querystring was chosen because it lists the parameters in the same order as the HTML.
        # However, it only includes the checkboxes that are checked.
        return redirect('search', GET_args = '?' + request.META['QUERY_STRING'])
    else:
        if str(request.GET) == '<QueryDict: {}>':
            increment_hit_count(request, "advanced_search")
    return render(request, 'en/public/advanced_search.html', {'form':form})
