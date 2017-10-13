# Description: This page redirects the user to a random slide page.

from Meowseum.models import Upload
from Meowseum.common_view_functions import redirect, get_public_unmuted_uploads, increment_hit_count
from random import randint

# 0. Main function
def page(request):
    increment_hit_count(request, 'random_slide')
    public_unmuted_uploads = get_public_unmuted_uploads(request.user)
    count = public_unmuted_uploads.count()
    if count < 2:
        # Redirect to the front page if there is only one upload, because if that upload is deleted, an infinite recursion error will occur.
        return redirect('index')
    else:
        relative_url = get_random_relative_url(public_unmuted_uploads, count)
        # For the slide page, indicate that the user navigated from the "Random upload" link instead of a gallery page.
        if 'current_gallery' in request.session:
            del request.session['current_gallery']
        request.session['random'] = True
        return redirect('slide_page', args=[relative_url])

# 1. Retrieve a random relative URL in the Pets category.
def get_random_relative_url(public_unmuted_uploads, count):
    # The function is recursive in order to solve a rare exception problem. When the number of uploads in the database drops between
    # calculating the count and making the random query, there is a chance of getting an index higher than the highest index in the list.
    # Keep querying for a random pet cat until the query doesn't cause an exception. Infinite recursion will occur if the amount of pet cats in the database drops to 0.
    random_index = randint(0, count - 1)
    try:
        return public_unmuted_uploads[random_index].relative_url
    except IndexError:
        # If the number of uploads in the database has changed since the count was calculated,
        # because an upload has been deleted since then, then keep trying until the program is able to access a random upload.
        return get_random_relative_url(count)
