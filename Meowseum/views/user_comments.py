# Description: This page shows all of a user's comments, each to the right of the image on which the user commented.

from django.contrib.auth.decorators import login_required
from Meowseum.models import Upload, Comment, hosting_limits_for_Upload
from django.contrib.auth.models import User
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from Meowseum.common_view_functions import increment_hit_count
from Meowseum.common_view_functions import get_public_unmuted_uploads

@login_required
def your_comments(request):
    # Shortcut for the link in the header
    return redirect('user_comments', args=[request.user.username])

# 0. Main function.
def page(request, username):
    template_variables = {}
    increment_hit_count(request, 'user_comments')
    # Send the username to the template in order to use it in the navigation bar.
    template_variables['profile_username'] = username

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

    template_variables['user_profile'] = user.user_profile
    template_variables['viewer_username'] = request.user.username
    # The first part of this predicate prevents an exception from occurring when the user is logged out and has no user_profile.
    if request.user.is_authenticated() and user.user_profile in request.user.user_profile.following.all():
        template_variables['following'] = True
    else:
        template_variables['following'] = False
    if request.POST:
        # If a logged in user clicks the option in the dropdown, then the logged in user follows or unfollows this user's gallery.
        if request.user.is_authenticated():
            if user.user_profile in request.user.user_profile.following.all():
                request.user.user_profile.following.remove(user.user_profile)
                template_variables['following'] = False
            else:
                request.user.user_profile.following.add(user.user_profile)
                request.user.user_profile.muting.remove(user.user_profile)
                template_variables['following'] = True
            request.user.user_profile.save()
        else:
            # Redirect the user to the login page, then back to this gallery after the user logs in.
            return redirect('login', query = 'next=' + reverse('user_comments', args=[request.user.username]))
        
    template_variables = paginate_queryset(request, comments, 'comments', no_results_message, template_variables)
    return render(request, 'en/public/user_comments.html', template_variables)

# 1. Paginate a queryset into pages of 25 results. Store into the template_variables dictionary the following values: 1) the queryset 2) a message to be displayed if there are no results.
def paginate_queryset(request, queryset, queryset_name, no_results_message, template_variables):
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    try:
        paginated_queryset = paginator.page(page)
    except PageNotAnInteger:
        paginated_queryset = paginator.page(1)
    except EmptyPage:
        paginated_queryset = paginator.page(paginator.num_pages)

    template_variables[queryset_name] = paginated_queryset
    template_variables['upload_directory'] = Upload.UPLOAD_TO
    template_variables['thumbnail_directory'] = hosting_limits_for_Upload['thumbnail'][2]
    template_variables['poster_directory'] = hosting_limits_for_Upload['poster_directory']
    template_variables['no_results_message'] = no_results_message
    return template_variables
