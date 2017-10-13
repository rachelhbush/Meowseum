# Description: The first section of this file contains utility functions for views, like an extension of redirect(). The second part contains utility functions that are more
# specific to the site models, like retrieving uploads from unmuted users. Some of these are used in only two views, but they're here because Python does not allow two files to mutually
# import from one another. There are separate files for filter functions and functions related to handling files.

from Meowseum.models import Upload, Page, Like, hosting_limits_for_Upload
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.shortcuts import redirect as default_redirect
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.http import urlquote_plus
from django.http import HttpResponse
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
import datetime
from django.db.models import Count
from django.utils import timezone
import json

# Section 1. Utility functions.

# A. Extend Django's default redirect() shortcut with the ability to specify GET parameters and arguments.
# The GET_args argument can be in the form of a tuple of 2-tuples, a dictionary, an ordered dictionary, or a querystring.
# The querystring is expected to start with ? and already have its arguments properly encoded.
def redirect(to, GET_args=None, *args, **kwargs):
    if GET_args == None:
        return default_redirect(to, *args, *kwargs)
    else:
        querystring = get_querystring_from_data_structure(GET_args)
        return redirect_with_querystring(to, querystring, *args, **kwargs)
            
# A1. Construct a querystring from GET parameters and arguments via various data structures. Test in the Python shell.
# Input: GET_args, a tuple of 2-tuples, a dictionary, an ordered dictionary, or a querystring starting with ?.
# The querystring is expected to start with ? and already have its arguments properly encoded.
# Output: querystring
def get_querystring_from_data_structure(GET_args):
    if GET_args.__class__.__name__ == 'tuple':
        querystring = get_querystring_from_tuples(GET_args)
    elif GET_args.__class__.__name__ == 'dict' or GET_args.__class__.__name__ == 'OrderedDict':
        querystring = get_querystring_from_dict(GET_args)
    else:
        # The user supplied the GET arguments as a querystring.
        querystring = GET_args
    return querystring

# 1.1. Input: Tuple of 2-tuples. Output: Querystring.
def get_querystring_from_tuples(GET_args):
    if len(GET_args) > 0:
        querystring = '?'
        for x in range(len(GET_args)-1):
            querystring = querystring + urlquote_plus(GET_args[x][0], safe='/') + '=' + urlquote_plus(GET_args[x][1], safe='/') + '&'
        querystring = querystring + urlquote_plus(GET_args[len(GET_args)-1][0], safe='/') + '=' + urlquote_plus(GET_args[len(GET_args)-1][1], safe='/')
        return querystring
    else:
        return ''

# 1.2. Input: Dictionary or an ordered dictionary. Output: Querystring.
def get_querystring_from_dict(GET_args):
    if len(GET_args) > 0:
        querystring = '?'
        keys = tuple(GET_args.keys())
        values = tuple(GET_args.values())
        for x in range(len(GET_args)-1):
            querystring = querystring + urlquote_plus(keys[0], safe='/') + '=' + urlquote_plus(values[0], safe='/') + '&'
        querystring = querystring + urlquote_plus(keys[len(GET_args)-1], safe='/') + '=' + urlquote_plus(values[len(GET_args)-1], safe='/')
        return querystring
    else:
        return ''

# B0. Use this function when the request may be made with AJAX and the server determines that the user needs to be redirected to another page.
# The function will return a JSON object which will let a JavaScript function know to redirect the user. When the response is HTML being
# loaded into an element like a modal, and the page redirects to another page which will be loaded into the same element, then redirect directly.
# Input: request, url.
# Output: JSON object.
def ajaxWholePageRedirect(request, url):
    if request.is_ajax():
        response = {'status':0, 'message': "Redirecting", 'url':url}
        return HttpResponse(json.dumps(response), content_type='application/json')
    else:
        return default_redirect(url)

# 2. Redirect.
# Input: to, a page name or a URL. querysting, a string beginning with '?'.
# Output: Redirect response.
def redirect_with_querystring(to, querystring, *args, **kwargs):
    try:
        # If this works, the 'to' argument is a page name.
        return default_redirect(reverse(to) + querystring, *args, **kwargs)
    except NoReverseMatch:
        # The 'to' argument is a URL.
        return default_redirect(to + querystring, *args, *kwargs)

# Increment the hit count, using settings for the django-hitcounts add-on specified in the site's settings.py file.
# Input: request, the name of the page in urls.py, and a list of arguments for the page.
# Output: None.
def increment_hit_count(request, name, args=None):
    if args == None:
        record = Page.objects.get_or_create(name=name)[0]
    else:
        record = Page.objects.get_or_create(name=name, argument1=args[0])[0]
    hit_count = HitCount.objects.get_for_object(record)
    hit_count_response = HitCountMixin.hit_count(request, hit_count)
    return

# Section 2. Site functions. The sorting functions are used by gallery pages which specifically use the sorting order, and they're included here because in the
# future they'll be an option in the advanced search menu.

# This function filters out private uploads and uploads from muted users. This function is used by any view which displays a gallery, including the search page.
# Input: logged_in_user (request.user). Output: upload_queryset.
def get_public_unmuted_uploads(logged_in_user):
    upload_queryset = Upload.objects.filter(is_publicly_listed=True)
    if logged_in_user.is_authenticated():
        upload_queryset = upload_queryset.exclude(uploader__user_profile__in=logged_in_user.user_profile.muting.all())
    return upload_queryset

# Sort by all-time popularity on the site. Currently, this is identical to sort_by_likes(), but it may factor in the number of views in the future.
def sort_by_popularity(upload_queryset):
    return upload_queryset.annotate(number_of_likes=Count('likes')).order_by("-number_of_likes")

# Sort by recent popularity. Right now, this returns only the uploads sorted by the number of likes within the past week.
# Ideally, this would sort by how fast the upload is gaining popularity.
def sort_by_trending(upload_queryset):
    past_weeks_likes = Like.objects.filter(datetime_liked__gte = timezone.now() - datetime.timedelta(7))
    uploads_liked_in_past_week = upload_queryset.filter(likes__in=past_weeks_likes).annotate(number_of_likes=Count('likes')).order_by("-number_of_likes")
    uploads_not_liked_in_past_week = upload_queryset.exclude(likes__in=past_weeks_likes)
    upload_queryset = uploads_liked_in_past_week | uploads_not_liked_in_past_week
    return upload_queryset

# Sort by the all-time number of likes. This is intended to be used with a menu item explicitly specifying likes, but I haven't used it anywhere. 
def sort_by_likes(upload_queryset):
    return upload_queryset.annotate(number_of_likes=Count('likes')).order_by("-number_of_likes")

# Organize the list of uploads into pages with 25 uploads each. Store the relative URLs into a session variable in order to be able to navigate the queryset on slide pages.
# Input: request, list_of_uploads. no_results_message is a message to display when there are no uploads matching the query. template_variables dictionary
# Session variable output: current_gallery contains the list of relative URLs (after /slide/) for results in the gallery last viewed.
# index will indicate the index of the result while navigating slide pages. The program stores -1 to indicate that no slide has been visited yet.
# View output: The object which renders the template.
def generate_gallery(request, list_of_uploads, no_results_message, template_variables):
    paginator = Paginator(list_of_uploads, 25)
    page = request.GET.get('page')
    try:
        paginated_list_of_uploads = paginator.page(page)
    except PageNotAnInteger:
        paginated_list_of_uploads = paginator.page(1)
    except EmptyPage:
        paginated_list_of_uploads = paginator.page(paginator.num_pages)

    template_variables['uploads'] = paginated_list_of_uploads
    template_variables['upload_directory'] = Upload.UPLOAD_TO
    template_variables['thumbnail_directory'] = hosting_limits_for_Upload['thumbnail'][2]
    template_variables['poster_directory'] = hosting_limits_for_Upload['poster_directory']
    template_variables['no_results_message'] = no_results_message
    current_gallery = []
    for x in range(len(list_of_uploads)):
        current_gallery = current_gallery + [list_of_uploads[x].relative_url]
    # Store the list of relative URLs for each upload and the index of the previously viewed upload into a session variable.
    request.session['current_gallery'] = current_gallery
    if 'random' in request.session:
        # Delete a session storage variable that is used by the slide page to indicate that the user came from the "Random cat" page.
        del request.session['random']
    return render(request, 'en/public/gallery.html', template_variables)
