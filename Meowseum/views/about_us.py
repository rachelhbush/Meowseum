from Meowseum.common_view_functions import increment_hit_count
from django.shortcuts import render

def page(request):
    increment_hit_count(request, "about_us")
    return render(request, 'en/public/about_us.html')
