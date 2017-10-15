# Description: Each view in this file defines a queryset or list of records and then passes it to a function which will paginate it and return the template.
# Results are usually sorted from newest to oldest, for pages like a user's upload gallery. Views that use a different sorting order will mention it in the view's description.

from django.contrib.auth.decorators import login_required
from Meowseum.models import Upload, Like, Tag
from django.contrib.auth.models import User
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from django.core.urlresolvers import reverse
from operator import attrgetter
from django.db.models import Count
import datetime
from Meowseum.common_view_functions import get_public_unmuted_uploads, generate_gallery, increment_hit_count, sort_by_popularity, sort_by_trending
from Meowseum.views.search import get_search_queryset

# 0. Main function for the front page. If the user is logged out, then this is the same as the highest rated page.
# If the user is logged in, then this is the same as the followed user page.
def front_page(request):
    increment_hit_count(request, "index")
    if request.user.is_authenticated():
        if 'saved_search' in request.session:
            return process_saved_search(request)
        else:
            return front_page_most_popular(request)
    else:
        if 'saved_search' in request.session:
            return process_saved_search(request)
        else:
            return front_page_most_popular(request)

# 1. Retrieve the results from the user's saved search.
def process_saved_search(request):
    form = request.session['saved_search']
    list_of_uploads = list(get_search_queryset(form, request.user))
    context = {}
    return generate_gallery(request, list_of_uploads, "No results were found matching your search.", context)

# 2. This is a copy of the 'subscribed_tags' view, used for redirecting from the front page so the hit count won't be incremented.
def front_page_subscribed_tags(request):
    upload_queryset = get_public_unmuted_uploads(request.user)
    subscribed_tags = request.user.user_profile.subscribed_tags.all()
    upload_queryset = upload_queryset.filter(tags__in=subscribed_tags)
    upload_queryset = list(sort_by_trending(upload_queryset))
    context = {}
    return generate_gallery(request, upload_queryset, "You haven't subscribed to a tag yet.", context)

# 3. This is a copy of the 'most_popular' view, used for redirecting from the front page so the hit count won't be incremented.
def front_page_most_popular(request):
    upload_queryset = get_public_unmuted_uploads(request.user)
    upload_queryset = list(sort_by_trending(upload_queryset))
    context = {}
    return generate_gallery(request, upload_queryset, "Nothing has been uploaded to the site yet.", context)

# Main function for the 'most_popular' page, which uses the site's trending algorithm.
def most_popular(request):
    increment_hit_count(request, "most_popular")
    upload_queryset = get_public_unmuted_uploads(request.user)
    upload_queryset = list(sort_by_trending(upload_queryset))
    context = {}
    return generate_gallery(request, upload_queryset, "Nothing has been uploaded to the site yet.", context)

# Main function for the 'new_submissions' page.
def new_submissions(request):
    increment_hit_count(request, "new_submissions")
    # Retrieve uploads ordered from latest to earliest.
    upload_queryset = get_public_unmuted_uploads(request.user)
    upload_queryset = list(upload_queryset.order_by("-id"))
    context = {}
    return generate_gallery(request, upload_queryset, "Nothing has been uploaded to the site yet.", context)

# Main function for the gallery for each tag. Results are sorted using the site's trending algorithm.
def tag_gallery(request, tag_name):
    increment_hit_count(request, "tag_gallery", [tag_name])
        
    try:
        tag = Tag.objects.get(name=tag_name.lower())
        upload_queryset = get_public_unmuted_uploads(request.user)
        upload_queryset = upload_queryset.filter(tags=tag)
        upload_queryset = list(sort_by_trending(upload_queryset))
        if request.user.is_authenticated() and tag in request.user.user_profile.subscribed_tags.all():
            subscribed = True
        else:
            subscribed = False
    except Tag.DoesNotExist:
        upload_queryset = []
        tag = None
        subscribed = None

    context = {'tag': tag, 'subscribed': subscribed}
    return generate_gallery(request, upload_queryset, "No uploads currently have this tag.", context)

@login_required
def your_uploads(request):
    # Shortcut for the link in the header. This exists because it is currently faster than having request.user stored as a variable in the template on every page.
    return redirect('gallery', request.user.username)

# Main function for the 'gallery' page.
def uploads(request, username):
    increment_hit_count(request, "gallery", [username])
    # Retrieve the queryset of uploads from the owner of the profile. If the viewer isn't the owner of the profile,
    # then first filter down to the public uploads from unmuted users. The viewer sees nothing if the viewer is muting the profile owner.
    user = User.objects.get(username=username)
    if user == request.user:
        upload_queryset = request.user.uploads.all()
        no_results_message = "You haven't uploaded anything yet."
    else:
        upload_queryset = get_public_unmuted_uploads(request.user).filter(uploader=user)
        no_results_message = "This user hasn't uploaded anything yet."
    upload_queryset = list(upload_queryset.order_by("-id"))

    # Check whether the user is following the owner of the profile.
    # The first part of this predicate prevents an exception from occurring when the user is logged out and has no user_profile.
    if request.user.is_authenticated() and user.user_profile in request.user.user_profile.following.all():
        following = True
    else:
        following = False

    context = {'gallery_type': 'uploads',
               'profile_username': username,
               'user_profile': user.user_profile,
               'viewer_username': request.user.username,
               'following': following}
    return generate_gallery(request, upload_queryset, no_results_message, context)

@login_required
def your_likes(request):
    # Shortcut for the link in the header
    return redirect('likes', request.user.username)

# Main function for the 'likes' page.
def likes(request, username):
    increment_hit_count(request, "gallery", [username])
    # Begin retrieving the list of like records for the user specified by the URL.
    user = User.objects.get(username=username)
    # Retrieve public, unmuted uploads, excluding the user's own uploads.
    relevant_uploads = get_public_unmuted_uploads(request.user).exclude(uploader=user)
    # Retrieve the list of Like records, with the most recent Likes listed first.
    users_likes = list(user.likes.filter(upload__in=relevant_uploads).order_by("-id"))
    # Retrieve the corresponding upload records, which will be ordered by the recency with which the user liked them.
    list_of_uploads = []
    for x in range(len(users_likes)):
        list_of_uploads = list_of_uploads + [users_likes[x].upload]
    
    if user == request.user:
        no_results_message = "You haven't Liked any uploads yet."
    else:
        no_results_message = "This user hasn't Liked any uploads yet."

    # Check whether the user is following the owner of the profile.
    # The first part of this predicate prevents an exception from occurring when the user is logged out and has no user_profile.
    if request.user.is_authenticated() and user.user_profile in request.user.user_profile.following.all():
        following = True
    else:
        following = False

    context = {'gallery_type': 'likes',
               'profile_username': username,
               'user_profile': user.user_profile,
               'viewer_username': request.user.username,
               'following': following}
    return generate_gallery(request, list_of_uploads, no_results_message, context)

# Main function for the 'from followed users' page.
@login_required
def from_followed_users(request):
    increment_hit_count(request, "followed_users")
    followed_user_profiles = request.user.user_profile.following.all()
    upload_queryset = get_public_unmuted_uploads(request.user)
    upload_queryset = upload_queryset.filter(uploader__user_profile__in=followed_user_profiles).order_by("-id")
    upload_list = list(upload_queryset)
            
    if len(followed_user_profiles) == 0:
        no_results_message = "You haven't followed any users yet."
    else:
        no_results_message = "None of your followed users have uploaded anything yet."
    context = {}
    return generate_gallery(request, upload_list, no_results_message, context)

# Main function for the 'subscribed_tags' page. Results are sorted using the site's trending algorithm.
@login_required
def subscribed_tags(request):
    increment_hit_count(request, "subscribed_tags")
    upload_queryset = get_public_unmuted_uploads(request.user)
    subscribed_tags = request.user.user_profile.subscribed_tags.all()
    upload_queryset = upload_queryset.filter(tags__in=subscribed_tags)
    upload_queryset = list(sort_by_trending(upload_queryset))
    context = {}
    return generate_gallery(request, upload_queryset, "You haven't subscribed to a tag yet.", context)
