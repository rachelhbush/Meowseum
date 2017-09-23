from django.shortcuts import render

# Default view. Deliver the template without any Django effects.
def page(request):
    return render(request, 'en/public/shelter_search.html')
