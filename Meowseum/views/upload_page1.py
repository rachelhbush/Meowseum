# upload_page1_v0_0_29.py by Rachel Bush. Date last modified: 7/4/2017 11:31 PM
# PROGRAM ID: upload_page1.py (_v0_0_29) / Upload from device form
# REMARKS: This form is for adding a title, description, and tags to the most recent file that a user uploaded.
# VERSION REMARKS: I'm transitioning the website from Scrapbin back to Meowseum and importing from project version 0.0.5.1 all the
# models I previously removed.

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from Meowseum.models import Upload, hosting_limits_for_Upload, Tag, Like, Shelter, UserContact
from Meowseum.forms import UploadPage1
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
import os
from django.conf import settings
from Meowseum.file_handling.CustomStorage import get_valid_file_name
from Meowseum.file_handling.file_utility_functions import make_unique_with_random_id_suffix_within_character_limit, file_name_and_url_will_be_unique, move_file

CONTACT_INFO_ERROR = mark_safe("""<div class="form-unit" id="contact-record-warning">To be able to make a listing, first we need your <a href='/user_contact_information' class="emphasized" target="_blank">contact \
information</a>. This information will allow other users to search for listings by geographic location. Shelters and rescue groups will contact you if they have helpful information \
related to your post (found a lost pet, etc). If you are a shelter, <a href='/shelter_contact_information' class="emphasized" target="_blank">register here</a>.</div>""")

# 0. Main function.
@login_required
def page(request):
    template_variables = {}
    # Try to get the logged-in user's most recent file submission.
    # If the user is logged out or hasn't submitted a file yet, then redirect to the homepage.
    try:
        record = Upload.objects.filter(uploader=request.user).order_by("-id")[0]
        template_variables['upload'] = record
    except IndexError:
        return HttpResponseRedirect(reverse('index'))
    
    template_variables['heading'] = "Uploading " + record.metadata.original_file_name + record.metadata.original_extension
    template_variables['upload_directory'] = Upload.UPLOAD_TO
    template_variables['poster_directory'] = hosting_limits_for_Upload['poster_directory']
    has_contact_information = determine_if_user_has_contact_information(request.user)
    template_variables['has_contact_information'] = has_contact_information
    template_variables['CONTACT_INFO_ERROR'] = CONTACT_INFO_ERROR
    
    if request.POST:
        # The user accessed the view by sending a POST request (form). Create a Form object from the request data and validate the form.
        form = UploadPage1(request.POST)
        if request.POST.get('upload_type') != 'pets' and not has_contact_information:
            form.add_error('upload_type', CONTACT_INFO_ERROR)
        if form.is_valid():
            update_and_save_upload_record(form, record)
            rename_upload_file(record, hosting_limits_for_Upload['poster_directory'])
            # Users will automatically Like their own uploads. Use get_or_create because there is nothing stopping a user from
            # going back to this page again after the upload has been submitted and using it to edit the user's most recent upload, even though when
            # the editing feature is introduced, it will use a separate view.
            Like.objects.get_or_create(upload=record, liker=request.user)
            return redirect_to_next_page(form.cleaned_data['upload_type'], record.relative_url)
        else:
            # Return the form with error messages.
            template_variables['form'] = form
            return render(request, 'en/public/upload_page1.html', template_variables)
    else:
        # The user accessed the view by navigating to it.
        form = UploadPage1(initial={"upload_type":"pets", "tags":"#"})
        template_variables['form'] = form
        return render(request, 'en/public/upload_page1.html', template_variables)

# 1. Detect whether the user is a shelter or has a contact information record on file.
# The returned value will be sent to the template, even if the user hasn't yet submitted the form yet. That way, the user will be warned to fill out
# contact information when he or she first presses Adoption, Lost, or Found, which is easier than filling out the rest of the information and the
# form returning an error.
def determine_if_user_has_contact_information(user):
    try:
       Shelter.objects.get(account = user)
       return True
    except ObjectDoesNotExist:
        try:
            UserContact.objects.get(account = user)
            return True
        except ObjectDoesNotExist:
            return False

# 2. Update the upload record with the title, description, tags, and whether or not the upload is publicly listed, then save.
def update_and_save_upload_record(form, record):
    record.title = form.cleaned_data['title']
    record.description = form.cleaned_data['description']
    record.is_publicly_listed = form.cleaned_data['is_publicly_listed']
    record.uploader_has_disabled_comments = form.cleaned_data['uploader_has_disabled_comments']

    tags_from_title_and_description = get_tags_from_title_and_description(form.cleaned_data['title'], form.cleaned_data['description'])
    tags_from_tag_form = get_tags_from_tag_form(form.cleaned_data['tags'])
    # Merge the list of checked popular tags, the tags that the user typed into the title and description fields, and the tags that the user typed into the form in the tags section.
    # Convert to a set in order to make sure that all tags are unique.
    tag_set = set(form.cleaned_data['popular_tags'] + tags_from_title_and_description + tags_from_tag_form)
    
    for tag in tag_set:
        try:
            # If the tag does exist, then associate this upload record with it.
            existing_tag = Tag.objects.get(name=tag)
            existing_tag.uploads.add(record)
            existing_tag.save()
        except ObjectDoesNotExist:
            # If the tag doesn't exist, create a new one and add the most recent upload as the first record.
            new_tag = Tag(name=tag)
            new_tag.save()
            new_tag.uploads.add(record)
            new_tag.save()
    record.save()

# 2.1. Input: title and description strings. Output: A list of tags using the format ["blep", "catloaf"]. All tags are stored in lowercase form.
def get_tags_from_title_and_description(title, description):
    word_list = title.split() + description.split()
    tag_list = []
    for x in range(len(word_list)):
        if is_hashtag(word_list[x]):
            tag_list = tag_list + [word_list[x].lstrip("#").lower()]
    return tag_list

# 2.1.1. Return True or False depending on whether the string follows the standard hashtag conventions. It should start with a #, then the next letter should be a letter or underscore,
# and the rest of the characters should be alphanumeric.
def is_hashtag(string):
    if string[0] == "#" and (string[1].isalpha() or string[1] == '_') and string[2:].isalnum():
        return True
    else:
        return False

# 2.2. Input: A valid comma-delimited string of tags for an upload, such as "#blep, #catloaf".
# Tags are case insensitive and stored as all lowercase in the database. Output: A list of tags using the format ["blep", "catloaf"].
def get_tags_from_tag_form(string):
    tag_list = string.split(",")
    for x in range(len(tag_list)):
        tag_list[x] = tag_list[x].lstrip(" ").lstrip("#").lower()
        # If the tag is a null string, because the user didn't enter anything, then remove the tag.
        if tag_list[x] == "":
            del tag_list[x]
    return tag_list

# 3. Rename the upload's file using up to 182 of the first characters of its title. If the file name already exists, then add an underscore and 7-character random ID
# to the end, replacing characters of the title if it is needed to stay within the limit. This function also accounts for the underscore-using, file name-based URL needing to be unique.
def rename_upload_file(record, poster_directory):
    # Obtain all the strings that will be used for renaming.
    upload_directory_name = os.path.split(record.file.name)[0]
    upload_directory_path = os.path.join(settings.MEDIA_PATH, upload_directory_name)
    old_file_name = record.metadata.file_name
    extension = record.metadata.extension
    new_file_name = get_new_file_name(record)
    old_full_file_name = old_file_name + extension
    new_full_file_name = new_file_name + extension
    
    # Rename the file in the OS.
    old_absolute_path = os.path.join(upload_directory_path, old_full_file_name)
    new_absolute_path = os.path.join(upload_directory_path, new_full_file_name)
    os.rename(old_absolute_path, new_absolute_path)
    # If the file is for a <video>, then rename its poster.
    if record.metadata.mime_type.startswith('video'):
        old_poster_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, old_file_name + '.jpg')
        new_poster_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, new_file_name + '.jpg')
        os.rename(old_poster_path, new_poster_path)
        
    # If a thumbnail exists in the OS, then rename the thumbnail.
    if record.metadata.width > 600:
        thumbnail_directory = hosting_limits_for_Upload['thumbnail'][2]
        old_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, thumbnail_directory, old_full_file_name)
        new_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, thumbnail_directory, new_full_file_name)
        os.rename(old_thumbnail_path, new_thumbnail_path)
        # If the file is for a <video>, then rename its thumbnail's poster.
        if record.metadata.mime_type.startswith('video'):
            old_poster_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, thumbnail_directory, old_file_name + '.jpg')
            new_poster_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, thumbnail_directory, new_file_name + '.jpg')
            os.rename(old_poster_thumbnail_path, new_poster_thumbnail_path)

    old_exif_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, 'metadata', old_file_name + '.dat')
    new_exif_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, 'metadata', new_file_name + '.dat')
    move_file(old_exif_path, new_exif_path)

    # Rename the file in Django's database.
    new_relative_path = os.path.join(upload_directory_name, new_file_name + extension).replace('\\','/') # This is the part of the path after /media/.
    record.file.name = new_relative_path
    record.relative_url = new_file_name.replace(" ","_")
    record.save()
    record.metadata.file_name = new_file_name
    record.metadata.save()

# 3.1 Return the new name for the file.
def get_new_file_name(record):
    hypothetical_file_name = record.title
    # Remove characters that are unsupported in a common operating system or may lead to security vulnerabilities.
    hypothetical_file_name = get_valid_file_name(hypothetical_file_name)
    if hypothetical_file_name == '_':
        # get_valid_file_name() makes sure that the file name can't be an empty string by adding an underscore.
        # make_unique_with_random_id_suffix_within_character_limit() returns a random ID if passed an empty string. 
        # Reset the underscore to an empty string, with the effect of disallowing '_' as a file name.
        hypothetical_file_name = ''
    return make_unique_with_random_id_suffix_within_character_limit(hypothetical_file_name, 178, file_name_and_url_will_be_unique, record)

# 4. After successfully processing the form, redirect to the homepage or the next page of the form if there is one.
# Input: upload_type, a string for the category. relative_url, a string which will be used when the upload is in the Pets category.
# In this case, the user doesn't need to fill out a second form, so the user will be redirected to the slide page for the new upload.
def redirect_to_next_page(upload_type, relative_url):
    if upload_type == "adoption":
        return HttpResponseRedirect(reverse('adoption_upload'))
    elif upload_type == "lost":
        return HttpResponseRedirect(reverse('lost_upload'))
    elif upload_type == "found":
        return HttpResponseRedirect(reverse('found_upload'))
    else:
        return HttpResponseRedirect(reverse('slide_page', args=[relative_url]))
