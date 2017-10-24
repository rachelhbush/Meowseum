# Description: The first section of this file contains utility functions for views, like an extension of redirect(). The second part contains utility functions that are more
# specific to the site models, like retrieving uploads from unmuted users. Some of these are used in only two views, but they're here because Python does not allow two files to mutually
# import from one another. There are separate files for filter functions and functions related to handling files.

from django.shortcuts import render, resolve_url
from django.shortcuts import redirect as original_redirect
from django.core.urlresolvers import reverse, NoReverseMatch
from urllib.parse import urlencode as original_urlencode
from urllib.parse import quote
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
import json
from django.http.request import QueryDict
from collections import OrderedDict
from django.utils.datastructures import MultiValueDict
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from Meowseum.models import Upload, Page, Like, hosting_limits_for_Upload
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import datetime
from django.db.models import Count
from django.utils import timezone

# Section 1. Utility functions.

class OrderedQueryDict(QueryDict, OrderedDict):
    pass

# 0. Extend Django's default redirect() shortcut with the ability to specify GET parameters and arguments.
# Input: to, a URL or page name. args, a list of arguments for Django's URL parameters. query can be any of various data structures, most usefully
# OrderedQueryDict, but it can also be a URL-encoded querystring, excluding the ?. The remaining input is less important and covered by Django documentation.
def redirect(to, *args, query=None, permanent=False, **kwargs):
    if query == None:
        return original_redirect(to, *args, *kwargs)
    else:
        querystring = urlencode(query)
        url = resolve_url(to, *args, **kwargs) + '?' + querystring
        # This somewhat repeats the definition of redirect() built into Django, which includes resolve_url().
        # This variation excludes resolve_url() to avoids the work of resolving the URL again.
        if permanent:
            redirect_class = HttpResponsePermanentRedirect
        else:
            redirect_class = HttpResponseRedirect
        return redirect_class(url)

# 0. Use this function when the request may be made with AJAX and the server determines that the user needs to be redirected to another page.
# The function will return a JSON object which will let a JavaScript function know to redirect the user. When the response is HTML being
# loaded into an element like a modal, and the page redirects to another page which will be loaded into the same element, then redirect directly.
# Input: request. to, a URL or page name. args, a list of arguments for Django's URL parameters. query can be any of various data structures, most usefully
# OrderedQueryDict, but it can also be a URL-encoded querystring, excluding the ?. The remaining input is less important and covered by Django documentation.
# Output: JSON object.
def ajaxWholePageRedirect(request, to,  *args, query=None, **kwargs):
    url = resolve_url(to, *args, **kwargs)
    if query != None:
        querystring = urlencode(query)
        url = url + '?' + querystring
        
    if request.is_ajax():
        response = {'status':0, 'message': "Redirecting", 'url':url}
        return HttpResponse(json.dumps(response), content_type='application/json')
    else:
        return HttpResponseRedirect(url)

# 1. Construct a querystring from GET parameters and arguments via various data structures. This is an extended version of urllib.parse.urlencode(). First, it includes
# changes from Django's version to support its dictionary classes with multiple values, rewritten for readability. Second, it returns the string if given a string, by assuming the
# querystring is already encoded, which makes can simplify functions by having to include one less branch. Third, it makes '/' exempt from URL encoding as %2F. This is nonstandard
# (see RFC 2396 sec. 2.2), but it's more readable and Django already does this in its built-in querystring for the login page. The last difference is that whether to encode ' ' as
# '%20' or '+', which is still '+' by default, is handled by a Boolean instead of passing a function object.
# Input: query. All the keyword arguments of Python's urlencode(), except using_plus instead of quote_via. Like the original function, if the input data type has ordering, the output
# querystring will use the same order. A data structure which simulates any form control will be equivalent to a list in which each element is a (string, list) tuple, such as Django's
# QueryDict class. This structure is necessary for fields which accept multiple values such as <select multiple> and checkboxes with the same name. If you are trying to emulate how Django
# renders a GET form as a querystring, remember that Django will render the value of a checked BooleanField checkbox (True) as 'on'.
# Output: querystring
def urlencode(query, *args, safe='/', using_plus=True, **kwargs):
    if query.__class__.__name__ == 'str':
        querystring = query
    else:
        if isinstance(query, MultiValueDict):
            query = query.lists()
        elif hasattr(query, 'items'):
            query = query.items()
        # After the preceding methods convert to an object similar to a tuple of 2-tuples with extra methods from the object's class, check whether each
        # second entry is a list or tuple. If this is the case, then standardize the data structure. Write it as list in which each entry is a 2-tuple
        # with a string for the first entry and a list or tuple for the second entry. Now urlencode can process extra classes such as dictionaries with
        # multiple values. This code related to this was adapted for readability from Django's extended version of urlencode under django.utils.http.
        # I removed code for supporting pre-Python 3.2 versions in which the encoding format wasn't a keyword argument, and I used longer variable names.
        query = [(key, [i for i in value] if isinstance(value, (list, tuple)) else value) for key, value in query]
        if using_plus:
            querystring = original_urlencode(query, *args, doseq=True, **kwargs)
        else:
            querystring = original_urlencode(query, *args, doseq=True, quote_via=quote, **kwargs)
    return querystring

# Generate a querystring from a form while listing the fields in the same order as the form's class definition. This function also allows
# excluding fields left blank by the user from the querystring in order to make the querystring more readable.
# If the form data has been altered during validation, the querystring will not be able to reflect any changes.
# Input: form, a Django form which has been filled out by the user. remove_blank_fields, a Boolean value.
#        safe, a string of characters to exclude from URL encoding. By default, this is '/'. Set to '' to exclude none.
# Output: ordered_querystring.
def get_ordered_querystring_from_form(form, excluding_blank_fields=False, safe='/'):
    ordered_query_dictionary = OrderedQueryDict(mutable=True)
    # Return a list of the form's fields in the same order as the form definition.
    list_of_fields = tuple(form.fields.keys())
    # Use the list to place values from the form.data's QueryDict into the OrderedQueryDict in the specified order.
    for x in range(len(list_of_fields)):
        field = list_of_fields[x]
        # Transfer the list of values associated with the field. The forms.data part of this line is why the querystring won't reflect changes to data during validation.
        # form.cleaned_data can't be used because, for example, a ModelChoiceField will contain an object and not the model IDs used for the querystring. 
        value = form.data.getlist(field)
        if value != [''] or not excluding_blank_fields:
            ordered_query_dictionary.setlist(field, value)
    return ordered_query_dictionary.urlencode(safe=safe)

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

# Input: request. records, a collection of records such as a queryset or list. records_per_page, an optional integer which defaults to 25.
# Output: paginated_records, a paginated collection of records.
def paginate_records(request, records, records_per_page=25):
    paginator = Paginator(records, records_per_page)
    page = request.GET.get('page')
    try:
        paginated_records = paginator.page(page)
    except PageNotAnInteger:
        paginated_records = paginator.page(1)
    except EmptyPage:
        paginated_records = paginator.page(paginator.num_pages)
    return paginated_records

# Section 2. Site functions. The sorting functions are used by gallery pages which specifically use the sorting order, and they're included here because in the
# future they'll be an option in the advanced search menu.

# This function filters out private uploads and uploads from muted users. This function is used by any view which displays a gallery, including the search page.
# Input: logged_in_user (request.user). Output: upload_queryset.
def get_public_unmuted_uploads(logged_in_user):
    upload_queryset = Upload.objects.filter(is_publicly_listed=True)
    if logged_in_user.is_authenticated:
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

# 0. Render a paginated gallery of Upload records. This function is invoked at the end of a view which gathers a collection of Uploads, such as those uploaded by user.
# At the end of each view, if there are any variables unique to the view, define a 'context' dictionary of variables to send to the template. This function will add to it
# the variables all Upload views should have in common. The 'context' dictionary should at least contain "no_results_message", a message to display if there are no uploads yet.
# Input: request. uploads, a collection of upload records. context, a dictionary of template variables unique to the view, containing a "no_results_message" key.
def render_upload_gallery(request, uploads, context):
    store_gallery_upload_relative_urls(request, uploads)
    paginated_uploads = paginate_records(request, uploads)
    
    context['uploads'] = paginated_uploads
    context['upload_directory'] = Upload.UPLOAD_TO
    context['thumbnail_directory'] = hosting_limits_for_Upload['thumbnail'][2]
    context['poster_directory'] = hosting_limits_for_Upload['poster_directory']
    return render(request, 'en/public/gallery.html', context)

# 1. For the gallery currently being viewed, store a list of unique upload relative URLs into session storage. This will allow the user to be able to navigate between
# uploads after visiting another page. The function also switches off a "random browsing" flag in session storage enabled by the random upload page.
# Input: request. uploads, an ordered collection of upload records for a gallery. This can be a queryset, list, tuple, etc.
# Output: None.
def store_gallery_upload_relative_urls(request, uploads):
    current_gallery = []
    for x in range(len(uploads)):
        current_gallery = current_gallery + [uploads[x].relative_url]
    # Store the list of relative URLs for each upload and the index of the previously viewed upload into a session variable.
    request.session['current_gallery'] = current_gallery
    if 'random' in request.session:
        # Delete a session storage variable that is used by the slide page to indicate that the user came from the "Random upload" page.
        del request.session['random']
