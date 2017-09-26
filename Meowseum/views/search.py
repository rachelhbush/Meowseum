# Description: This is the page for processing a search query and displaying the appropriate gallery of results.
# This includes both header searches and advanced searches.

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import get_public_unmuted_uploads, generate_gallery
from Meowseum.models import Upload, Metadata, Tag
from django.db.models.functions import Concat
from django.db.models import Value
from django.db.models import CharField
from django.db.models import Q
import operator
from functools import reduce
import datetime
from django.db.models import Count
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from urllib.parse import quote_plus
from Meowseum.common_view_functions import increment_hit_count

FORM_DICTIONARY = {'filtering_by_photos':'BooleanField',
                   'filtering_by_gifs':'BooleanField',
                   'filtering_by_looping_videos_with_audio':'BooleanField',
                   'min_duration':'FloatField',
                   'max_duration':'FloatField',
                   'min_fps':'FloatField',
                   'all_words':'CharField',
                   'exact_phrase':'CharField',
                   'any_words':'CharField',
                   'exclude_words':'CharField',
                   'from_user':'CharField',
                   'save_search_to_front_page':'BooleanField'}

# 0. Main function for queries from the search bar in the header. If the user enters a username, redirect to the gallery.
# Otherwise, redirect to the view for the advanced search page and use its "all words" field. This leaves open the possibility of programming
# other standard header search bar features, such as using " for an exact phrase or - for excluding, and breaking these down into values for the different advanced search fields.
def header_search(request):
    increment_hit_count(request, "header_search")
    header_search = request.GET.get('header_search')
    if header_search == '' or header_search == None:
        # The user didn't submit anything, which shouldn't be possible unless the user deleted all the arguments from the URL. Redirect to the front page.
        return HttpResponseRedirect(reverse('index'))
    elif header_search.startswith('@') and ' ' not in header_search:
        header_search = header_search.lstrip('@')
        try:
            username = User.objects.get(username = header_search).username
            # If the value is a valid username, redirect to the user page in a later version. Redirect to the user's gallery for now.
            return HttpResponseRedirect(reverse('gallery', args=[username]))
        except ObjectDoesNotExist:
            header_search = '@' + header_search
            # Adapt the user's input for transmission via URL and redirect to the main view for search queries.
            return HttpResponseRedirect(reverse('search') + "?" + "all_words=" + quote_plus(header_search))
    elif header_search.startswith('#') and ' ' not in header_search:
        header_search = header_search.lstrip('#')
        try:
            tag = Tag.objects.get(name = header_search)
            # If the value is a valid tag, redirect to the tag gallery page so the user will be able to subscribe/unsubscribe to the tag.
            return HttpResponseRedirect(reverse('tag_gallery', args=[tag.name]))
        except ObjectDoesNotExist:
            header_search = '#' + header_search
            return HttpResponseRedirect(reverse('search') + "?" + "all_words=" + quote_plus(header_search))
    else:
        return HttpResponseRedirect(reverse('search') + "?" + "all_words=" + quote_plus(header_search))

# 0. Main function for search queries.
def page(request):
    template_variables = {}
    increment_hit_count(request, "search")
    form = process_GET_form(request, FORM_DICTIONARY)
    if form['save_search_to_front_page']:
        if form_was_left_blank(form):
            if 'saved_search' in request.session:
                # If the user submitted a form that was left blank except for the "Save search to front page" checkbox, and the user has previously saved a search,
                # then delete the saved search setting and begin using the default front page again.
                del request.session['saved_search']
            # Redirect to the front page.
            return HttpResponseRedirect(reverse('index'))
        else:
            request.session['saved_search'] = form
    list_of_uploads = list(get_search_queryset(form, request.user))
    return generate_gallery(request, list_of_uploads, "No results were found matching your search.", template_variables)

# 1. Retrieve the values of the form from the querystring in the URL. For number fields, the value will be a string. Cast the values as the data type that will be used during querying.
# String fields use None as the default when the parameter isn't in the URL and an empty string when it is. The user may remove empty string arguments from the URL to make it shorter,
# so the program normalizes None to an empty string, except for number fields, which still use None for no value. For Boolean fields, if the field is checked, the value will be the string "on".
# The field will be absent if the checkbox is unchecked, so trying to retrieve its value will return None.
# Input: request and FORM_DICTIONARY, a constant matching all the names of the fields of the form with the field type.
# Output: A dictionary matching the names of the fields with their cast values.
def process_GET_form(request, FORM_DICTIONARY):
    output = {}
    for entry in FORM_DICTIONARY:
        value = request.GET.get(entry)
        if FORM_DICTIONARY[entry] == 'BooleanField':
            if value == 'on':
                output[entry] = True
            else:
                output[entry] = False
        elif FORM_DICTIONARY[entry] == 'FloatField':
            if value == '' or value == None:
                output[entry] = None
            else:
                output[entry] = float(value)
        elif FORM_DICTIONARY[entry] == 'IntegerField':
            if value == '' or value == None:
                output[entry] = None
            else:
                output[entry] = int(value)
        else:
            if value == None:
                # Normalize any unexpected argument in the URL into an empty string. The program expects this to be the format for indicating no value.
                value = ''
            output[entry] = value
    return output

# 2. Check if the form was left blank, excluding the "Save search to front page" checkbox. This function doesn't take into account values that would have
# the same effect as a blank form, such as only filling out '@' for the from field. Return True or False.
def form_was_left_blank(form):
    left_blank = True
    for entry in form:
        if form[entry] != None and form[entry] != '' and form[entry] != False and entry != 'save_search_to_front_page':
            left_blank = False
    return left_blank

# 3. Process the user's query into a queryset of Upload records. For now, results are sorted by newest to oldest. In the future, the user should be able to specify
# a sorting algorithm, including new, trending, and highest ranking.
def get_search_queryset(form, logged_in_user):
    upload_queryset = get_public_unmuted_uploads(logged_in_user)
    upload_queryset = process_metadata_queries(upload_queryset, form['filtering_by_photos'], form['filtering_by_gifs'], form['filtering_by_looping_videos_with_audio'],
                                               form['min_duration'], form['max_duration'], form['min_fps'])
    upload_queryset = process_word_queries(upload_queryset, form['all_words'], form['exact_phrase'], form['any_words'], form['exclude_words'])
    upload_queryset = filter_by_author(upload_queryset, form['from_user'])
    upload_queryset = upload_queryset.order_by("-id")
    return upload_queryset

# 3.1. Retrieve a queryset of uploads that takes into consideration all the fields related to the metadata for the upload file.
def process_metadata_queries(upload_queryset, filtering_by_photos, filtering_by_gifs, filtering_by_looping_videos_with_audio,
                             min_duration, max_duration, min_fps):
    upload_queryset = filter_by_file_type(upload_queryset, filtering_by_photos, filtering_by_gifs, filtering_by_looping_videos_with_audio)
    if not filtering_by_photos:
        upload_queryset = filter_by_video_metadata(upload_queryset, min_duration, max_duration, min_fps)
    return upload_queryset

# 3.1.1 Return the queryset of uploads that is filtered down to only the checked file types. This function only works for Meowseum's file hosting settings,
# where all images are JPEGs and all videos, including "GIFs", are MP4s.
def filter_by_file_type(upload_queryset, filtering_by_photos, filtering_by_gifs, filtering_by_looping_videos_with_audio):
    if (filtering_by_photos and filtering_by_gifs and filtering_by_looping_videos_with_audio) or (not filtering_by_photos and not filtering_by_gifs and not filtering_by_looping_videos_with_audio):
        # If all of the checkboxes are checked (filtering down to everything), then this is the same as if none of the checkboxes are checked. Do nothing to the queryset.
        pass
    elif filtering_by_photos and not filtering_by_gifs and not filtering_by_looping_videos_with_audio:
        upload_queryset = upload_queryset.filter(metadata__mime_type='image/jpeg')
    elif filtering_by_photos and filtering_by_gifs and not filtering_by_looping_videos_with_audio:
        # Exclude files that have sound.
        upload_queryset = upload_queryset.filter(metadata__has_sound=False)
    elif filtering_by_photos and not filtering_by_gifs and filtering_by_looping_videos_with_audio:
        upload_queryset = upload_queryset.filter(Q(metadata__mime_type='video/mp4', metadata__has_audio=True) | Q(metadata__mime_type='image/jpeg'))
    elif not filtering_by_photos and filtering_by_gifs and not filtering_by_looping_videos_with_audio:
        upload_queryset = upload_queryset.filter(metadata__mime_type='video/mp4', metadata__has_audio=False)
    elif not filtering_by_photos and filtering_by_gifs and filtering_by_looping_videos_with_audio:
        upload_queryset = upload_queryset.filter(metadata__mime_type='video/mp4')
    else:
        # The only remaining possibility is filtering down to only looping videos with sound.
        upload_queryset = upload_queryset.filter(metadata__mime_type='video/mp4', metadata__has_audio=True)
    return upload_queryset

# 3.1.2 Return a queryset in which the video uploads are filtered down using video-specific metadata.
def filter_by_video_metadata(upload_queryset, min_duration, max_duration, min_fps):
    if min_duration != None and min_duration != 0:
        # Include uploads with null values for the field so that image uploads will stay in the queryset.
        upload_queryset = upload_queryset.filter(Q(metadata__duration=None) | Q(metadata__duration__gte=min_duration))
    if max_duration != None:
        upload_queryset = upload_queryset.filter(Q(metadata__duration=None) | Q(metadata__duration__lte=max_duration))
    if min_fps != None and min_fps != 0:
        upload_queryset = upload_queryset.filter(Q(metadata__fps=None) | Q(metadata__fps__gte=min_fps))
    return upload_queryset

# 3.2. Retrieve a queryset of uploads using only the user's input for the standard four word-related fields in an advanced search query.
# For the search, use the combined text of the title and the description.
# Input: upload_queryset. all_words, exact_phrase, any_words, and exclude_words are all strings.
# Output: A modified queryset of Upload records.
def process_word_queries(upload_queryset, all_words, exact_phrase, any_words, exclude_words):
    if all_words != '' or exact_phrase != '' or any_words != '' or exclude_words != '':
        upload_queryset = upload_queryset.annotate(title_and_description=Concat('title', Value(' '), 'description', output_field=CharField()) )
        if all_words != '':
            hashtagless_list_of_words, list_of_tag_strings = separate_string_into_list_of_words_and_list_of_tag_strings(all_words)
            if len(list_of_tag_strings) > 0:
                upload_queryset = process_all_hashtags_query(upload_queryset, list_of_tag_strings)
            if len(hashtagless_list_of_words) > 0:
                upload_queryset = process_all_words_query(upload_queryset, hashtagless_list_of_words)
        if exact_phrase != '':
            upload_queryset = process_exact_phrase_query(upload_queryset, exact_phrase)
        if any_words != '':
            hashtagless_list_of_words, list_of_tag_strings = separate_string_into_list_of_words_and_list_of_tag_strings(any_words)
            if len(list_of_tag_strings) > 0:
                upload_queryset = process_any_hashtags_query(upload_queryset, list_of_tag_strings)
            if len(hashtagless_list_of_words) > 0:
                upload_queryset = process_any_words_query(upload_queryset, hashtagless_list_of_words)
        if exclude_words != '':
            hashtagless_list_of_words, list_of_tag_strings = separate_string_into_list_of_words_and_list_of_tag_strings(exclude_words)
            if len(list_of_tag_strings) > 0:
                upload_queryset = process_exclude_hashtags_query(upload_queryset, list_of_tag_strings)
            if len(hashtagless_list_of_words) > 0:
                upload_queryset = process_exclude_words_query(upload_queryset, hashtagless_list_of_words)
    return upload_queryset

# 3.2.1. Input: A string, particularly the combined text of the title and description.
# Output: hashtagless_list_of_words, a list of words in the string excluding the words beginning with a #. 'words' is loosely used to refer to a collection of characters separated by spaces.
# list_of_tag_strings, a list of words identified by starting with a #, but with the # removed.
def separate_string_into_list_of_words_and_list_of_tag_strings(string):
    list_of_words = string.split()
    list_of_tag_strings = []
    hashtagless_list_of_words = []
    for x in range(len(list_of_words)):
        if list_of_words[x].startswith('#'):
            list_of_tag_strings = list_of_tag_strings + [list_of_words[x].lstrip('#').lower()] # Hashtags are case insensitive by convention.
        else:
            hashtagless_list_of_words = hashtagless_list_of_words + [list_of_words[x]]
    
    return hashtagless_list_of_words, list_of_tag_strings

# 3.2.2. Input: Queryset of uploads, list of tag strings. Output: The uploads that contain all of the tags in the query, in no specific order.
def process_all_hashtags_query(upload_queryset, list_of_tag_strings):
    # Query for the tag records corresponding to each string in the list.
    tag_queryset = Tag.objects.filter(name__in=list_of_tag_strings)
    # Filter down to the uploads that have all of the tags. The first part filters down to uploads that have any of the tags.
    # The second part filters down to those where the upload's number of matching tags is equal to the number of tags in the query.
    # Count() looks at only the subset of the upload's tags that passed the prior filter().
    # See https://docs.djangoproject.com/en/1.10/topics/db/aggregation/#order-of-annotate-and-filter-clauses
    upload_queryset = upload_queryset.filter(tags__in=tag_queryset).annotate(num_tags=Count('tags')).filter(num_tags=tag_queryset.count())
    return upload_queryset

# 3.2.3. Return only the uploads that contain each word in the query, in no specific order, as if AND were between each.
def process_all_words_query(upload_queryset, all_words_list):
    # This statement allows avoiding making a separate query for each word.
    query = reduce(operator.and_, (Q(title_and_description__icontains = item) for item in all_words_list))
    upload_queryset = upload_queryset.filter(query)
    return upload_queryset

# 3.2.4. Return only the uploads that mention the exact phrase.
def process_exact_phrase_query(upload_queryset, exact_phrase):
    # Strip quotation marks around the whole input, because this is the notation for performing this action in the search bar.
    exact_phrase = exact_phrase.strip('"')
    return upload_queryset.filter(title_and_description__icontains = exact_phrase)

# 3.2.5. Input: Queryset of uploads, list of tag strings. Output: The uploads that contain any of the tags in the query, in no specific order.
def process_any_hashtags_query(upload_queryset, list_of_tag_strings):
    # Query for the tag records corresponding to each string in the list.
    tag_queryset = Tag.objects.filter(name__in=list_of_tag_strings)
    # Filter down to the uploads that have any of the tags.
    upload_queryset = upload_queryset.filter(tags__in=tag_queryset)
    return upload_queryset

# 3.2.6. Return only the uploads that contain any of the words in the query, as if OR were between each.
def process_any_words_query(upload_queryset, any_words_list):
    query = reduce(operator.or_, (Q(title_and_description__icontains = item) for item in any_words_list))
    upload_queryset = upload_queryset.filter(query)
    return upload_queryset

# 3.2.7. Input: Queryset of uploads, list of tag strings. Output: The uploads that exclude all of the tags in the query.
def process_exclude_hashtags_query(upload_queryset, list_of_tag_strings):
    # Query for the tag records corresponding to each string in the list.
    tag_queryset = Tag.objects.filter(name__in=list_of_tag_strings)
    # Exclude uploads that have any of the tags.
    upload_queryset = upload_queryset.exclude(tags__in=tag_queryset)
    return upload_queryset

# 3.2.8. Return only the uploads that exclude all of the words in the query, as if AND NOT were between each.
def process_exclude_words_query(upload_queryset, exclude_words_list):
    # Excluding uploads that have all of the words is the same as making sure they don't have any of them, so use the same query as in process_any_words_query().
    # The Django methods make it easy to see that the relationship between filter, exclude, any, and all follows DeMorgan's Laws.
    query = reduce(operator.or_, (Q(title_and_description__icontains = item) for item in exclude_words_list))
    upload_queryset = upload_queryset.exclude(query)
    return upload_queryset

# 3.3. Return only the uploads that were uploaded by a certain author.
def filter_by_author(upload_queryset, from_user):
    from_user = from_user.lstrip('@')
    if from_user == '':
        return upload_queryset
    else:
        return upload_queryset.filter(uploader__username = from_user)
