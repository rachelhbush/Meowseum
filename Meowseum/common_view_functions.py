# Description: This file contains all the functions that are common to multiple views, excluding those that are also used elsewhere by Django, such as filter functions used by templates.
# I had to create this file because Python does not allow two files to mutually import from one another.

from Meowseum.models import Upload, Page, Like, hosting_limits_for_Upload
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
import datetime
from django.db.models import Count
from django.utils import timezone
import json

# This function filters out private uploads and uploads from muted users. It is used by all galleries.
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

# Use this function when the request may be made with AJAX and the server determines that the user needs to be redirected to another page.
# The function will return a JSON object which will let a JavaScript function know to redirect the user. When the response is HTML being
# loaded into an element like a modal, and the page redirects to another page which will be loaded into the same element, then use HttpResponseRedirect directly.
def ajaxWholePageRedirect(request, url):
    if request.is_ajax():
        response = {'status':0, 'message': "Redirecting", 'url':url}
        return HttpResponse(json.dumps(response), content_type='application/json')
    else:
        return HttpResponseRedirect(url)
