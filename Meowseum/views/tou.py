from Meowseum.common_view_functions import increment_hit_count
from django.shortcuts import render

def page(request):
    increment_hit_count(request, "tou")
    return render(request, 'en/public/tou.html')
