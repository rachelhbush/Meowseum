# Description: This page shows all of a user's comments, each to the right of the image on which the user commented.

from django.contrib.auth.decorators import login_required
from Meowseum.models import Upload, Comment, hosting_limits_for_Upload
from django.contrib.auth.models import User
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import increment_hit_count, get_public_unmuted_uploads, paginate_records

@login_required
def your_comments(request):
    # Shortcut for the link in the header
    return redirect('user_comments', request.user.username)

# 0. Main function.
def page(request, username):
    increment_hit_count(request, 'user_comments')
    # Retrieve the queryset of comments from the owner of the profile. If the logged in user isn't the owner of the profile,
    # then filter the comments down to only the ones on public uploads from unmuted users.
    user = User.objects.get(username=username)
    comments = Comment.objects.filter(commenter=user)
    if user == request.user:
        no_results_message = "You haven't commented on an upload yet."
    else:
        public_unmuted_uploads = get_public_unmuted_uploads(request.user)
        comments = comments.filter(upload__in=public_unmuted_uploads)
        no_results_message = "This user hasn't commented on an upload yet."
    comments = comments.order_by("-id")

    # Check whether the user is following the owner of the profile.
    # The first part of this predicate prevents an exception from occurring when the user is logged out and has no user_profile.
    if request.user.is_authenticated and user.user_profile in request.user.user_profile.following.all():
        following = True
    else:
        following = False
        
    comments = paginate_records(request, comments)
    # Set up variables which will be used in the template.
    context = {'upload_directory': Upload.UPLOAD_TO,
               'thumbnail_directory': hosting_limits_for_Upload['thumbnail'][2],
               'poster_directory': hosting_limits_for_Upload['poster_directory'],
               'comments': comments,
               'no_results_message': no_results_message,
               # These template variables will be used for following the user whose profile is being viewed.
               'profile_username': username,
               'user_profile': user.user_profile,
               'viewer_username': request.user.username,
               'following': following}
    return render(request, 'en/public/user_comments.html', context)
