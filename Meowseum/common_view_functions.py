# Description: The first section of this file contains utility functions for views, like an extension of redirect(). The second part contains utility functions that are more
# specific to the site models, like retrieving uploads from unmuted users. Some of these are used in only two views, but they're here because Python does not allow two files to mutually
# import from one another. There are separate files for filter functions and functions related to handling files.

from django.shortcuts import render, resolve_url
from django.shortcuts import redirect as default_redirect
from django.core.urlresolvers import reverse, NoReverseMatch
from urllib.parse import urlencode
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
# Input: to, a URL or page name. args, a list of arguments for Django's URL parameters. GET_args can be any of various data structures, most usefully
# OrderedQueryDict, but it can also be a URL-encoded querystring beginning with ?. The remaining input is less important and covered by Django documentation.
def redirect(to, GET_args=None, *args, **kwargs):
    if GET_args == None:
        return default_redirect(to, *args, *kwargs)
    else:
        querystring = get_querystring_from_data_structure(GET_args)
        url = resolve_url(to, *args, **kwargs) + querystring
        # This somewhat repeats the definition of redirect() built into Django, which includes resolve_url().
        # This variation excludes resolve_url() to avoids the work of resolving the URL again.
        if kwargs.pop('permanent', False):
            redirect_class = HttpResponsePermanentRedirect
        else:
            redirect_class = HttpResponseRedirect
        return redirect_class(url)

# 0. Use this function when the request may be made with AJAX and the server determines that the user needs to be redirected to another page.
# The function will return a JSON object which will let a JavaScript function know to redirect the user. When the response is HTML being
# loaded into an element like a modal, and the page redirects to another page which will be loaded into the same element, then redirect directly.
# Input: request. to, a URL or page name. args, a list of arguments for Django's URL parameters. GET_args can be any of various data structures, most usefully
# OrderedQueryDict, but it can also be a URL-encoded querystring beginning with ?. The remaining input is less important and covered by Django documentation.
# Output: JSON object.
def ajaxWholePageRedirect(request, to, GET_args=None, *args, **kwargs):
    url = resolve_url(to, *args, **kwargs)
    if GET_args != None:
        querystring = get_querystring_from_data_structure(GET_args)
        url = url + querystring
        
    if request.is_ajax():
        response = {'status':0, 'message': "Redirecting", 'url':url}
        return HttpResponse(json.dumps(response), content_type='application/json')
    else:
        return HttpResponseRedirect(url)

# 1. Construct a querystring from GET parameters and arguments via various data structures. The exemption of '/' from URL encoding is nonstandard (see RFC 2396 sec. 2.2),
# but it works, it's more readable, many sites do it, and Django does this in its built-in querystring for the login page. This function can be tested in the Python shell.
# If you are trying to emulate how Django renders a GET form int oa querystring, remember that Django will render the value of a checked BooleanField checkbox (True) as 'on'.
# Input: GET_args. This can be one of the Django classes created in order to support dictionaries which can have multiple values, such as QueryDict, which are necessary for
# fields which accept multiple values such as <select multiple> and checkboxes with the same name. This can also be a tuple of 2-tuples, a dictionary, an ordered dictionary,
# or a querystring. If the input data type has ordering, the output querystring will use the same order. An input querystring is expected to start with ? and already have
# its arguments properly encoded. Unlike the path part of the URL, it's not possible to write a querystring without encoding while writing because the values might contain
# special characters like ?. This also helps because most of Django's methods such as reverse() already return an encoded URL, and encoding it twice would produce bad output.
# Output: querystring
def get_querystring_from_data_structure(GET_args, safe='/'):
    if GET_args.__class__.__name__ == 'str':
        querystring = GET_args
    else:
        if len(GET_args) > 0:
            if isinstance(GET_args, MultiValueDict):
                GET_args = GET_args.lists()
            elif hasattr(GET_args, 'items'):
                GET_args = GET_args.items()
            # After the preceding methods convert to an object similar to a tuple of 2-tuples with extra methods from the object's class, check whether each
            # second entry is a list or tuple. If this is the case, then standardize the data structure. Write it as list in which each entry is a 2-tuple
            # with a string for the first entry and a list or tuple for the second entry. Now urlencode can process extra classes such as dictionaries with
            # multiple values. This code related to this was adapted for readability from Django's extended version of urlencode under django.utils.http.
            GET_args = [(key, [i for i in value] if isinstance(value, (list, tuple)) else value) for key, value in GET_args]
            querystring = '?' + urlencode(GET_args, safe=safe, doseq=True)
        else:
            # The argument is an empty object, so return an empty string.
            return ''
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
