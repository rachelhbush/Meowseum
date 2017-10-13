from django.contrib.auth import logout
from Meowseum.common_view_functions import redirect

def page(request):
  logout(request)
  # After logging out, redirect to the front page.
  return redirect('index')
