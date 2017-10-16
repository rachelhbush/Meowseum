# REMARKS: Upload from device form. This form is for adding a title, description, and tags to the most recent file that a user uploaded.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from Meowseum.common_view_functions import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from Meowseum.models import Upload, hosting_limits_for_Upload, Tag, Like, Shelter, UserContact
from Meowseum.forms import UploadPage1, CONTACT_INFO_ERROR
import os
from django.conf import settings
from Meowseum.file_handling.CustomStorage import get_valid_file_name
from Meowseum.file_handling.file_utility_functions import make_unique_with_random_id_suffix_within_character_limit, file_name_and_url_will_be_unique, move_file

# 0. Main function.
@login_required
def page(request):
    # Try to get the logged-in user's most recent file submission.
    try:
        upload = Upload.objects.filter(uploader=request.user).order_by('-id')[0]
    except IndexError:
        # If the user hasn't submitted a file yet, then the user shouldn't be here.
        raise PermissionDenied
    
    form = UploadPage1(request.POST or None, initial={'upload_type':'pets', 'tags':'#'}, request=request)
    if form.is_valid():
        update_and_save_upload_record(form, upload)
        rename_upload_file(upload, hosting_limits_for_Upload['poster_directory'])
        # Users will automatically Like their own uploads. Use get_or_create because there is nothing stopping a user from
        # going back to this page again after the upload has been submitted and using it to edit the user's most recent upload, even though when
        # the editing feature is introduced, it will use a separate view.
        Like.objects.get_or_create(upload=upload, liker=request.user)
        return redirect_to_next_page(form.cleaned_data['upload_type'], upload.relative_url)
    else:
        # Send the following variables to the template.
        context = {'form': form,
                   'upload': upload,
                   'heading': 'Uploading ' + upload.metadata.original_file_name + upload.metadata.original_extension,
                   'upload_directory': Upload.UPLOAD_TO,
                   'poster_directory': hosting_limits_for_Upload['poster_directory'],
                   'has_contact_information': request.user.user_profile.has_contact_information(),
                   'CONTACT_INFO_ERROR': CONTACT_INFO_ERROR}
        return render(request, 'en/public/upload_page1.html', context)

# 2. Update the upload record with the title, description, tags, and whether or not the upload is publicly listed, then save.
def update_and_save_upload_record(form, upload):
    upload.title = form.cleaned_data['title']
    upload.description = form.cleaned_data['description']
    upload.is_publicly_listed = form.cleaned_data['is_publicly_listed']
    upload.uploader_has_disabled_comments = form.cleaned_data['uploader_has_disabled_comments']
    upload.save()
    update_tag_data(form, upload)

# 2.1. Use the tag part of the form to update the database.
def update_tag_data(form, upload):
    tags_from_title_and_description = get_tags_from_title_and_description(form.cleaned_data['title'], form.cleaned_data['description'])
    tags_from_tag_form = get_tags_from_tag_form(form.cleaned_data['tags'])
    # Merge the list of checked popular tags, the tags that the user typed into the title and description fields, and the tags that the user typed into the form in the tags section.
    # Convert to a set in order to make sure that all tags are unique.
    tag_set = set(form.cleaned_data['popular_tags'] + tags_from_title_and_description + tags_from_tag_form)
    
    for tag in tag_set:
        try:
            # If the tag does exist, then associate this upload record with it.
            existing_tag = Tag.objects.get(name=tag)
            existing_tag.uploads.add(upload)
        except Tag.DoesNotExist:
            # If the tag doesn't exist, create a new one and add the most recent upload as its first record.
            new_tag = Tag(name=tag)
            new_tag.save()
            new_tag.uploads.add(upload)

# 2.1.1. Input: title and description strings.
#        Output: tag_list, a list of tags using the format ["blep", "catloaf"]. All tags are stored in lowercase form.
def get_tags_from_title_and_description(title, description):
    word_list = title.split() + description.split()
    tag_list = []
    for x in range(len(word_list)):
        if is_hashtag(word_list[x]):
            tag_list = tag_list + [word_list[x].lstrip("#").lower()]
    return tag_list

# 2.1.1.1. Return True or False depending on whether the string follows the standard hashtag conventions. It should start with a #, then the next letter should be a letter or underscore,
# and the rest of the characters should be alphanumeric.
def is_hashtag(string):
    if string[0] == "#" and (string[1].isalpha() or string[1] == '_') and string[2:].isalnum():
        return True
    else:
        return False

# 2.1.2. Input: A valid comma-delimited string of tags for an upload, such as "#blep, #catloaf".
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
def rename_upload_file(upload, poster_directory):
    # Obtain all the strings that will be used for renaming.
    upload_directory_name = os.path.split(upload.file.name)[0]
    upload_directory_path = os.path.join(settings.MEDIA_PATH, upload_directory_name)
    old_file_name = upload.metadata.file_name
    extension = upload.metadata.extension
    new_file_name = get_new_file_name(upload)
    old_full_file_name = old_file_name + extension
    new_full_file_name = new_file_name + extension
    
    # Rename the file in the OS.
    old_absolute_path = os.path.join(upload_directory_path, old_full_file_name)
    new_absolute_path = os.path.join(upload_directory_path, new_full_file_name)
    os.rename(old_absolute_path, new_absolute_path)
    # If the file is for a <video>, then rename its poster.
    if upload.metadata.mime_type.startswith('video'):
        old_poster_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, old_file_name + '.jpg')
        new_poster_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, new_file_name + '.jpg')
        os.rename(old_poster_path, new_poster_path)
        
    # If a thumbnail exists in the OS, then rename the thumbnail.
    if upload.metadata.width > 600:
        thumbnail_directory = hosting_limits_for_Upload['thumbnail'][2]
        old_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, thumbnail_directory, old_full_file_name)
        new_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, thumbnail_directory, new_full_file_name)
        os.rename(old_thumbnail_path, new_thumbnail_path)
        # If the file is for a <video>, then rename its thumbnail's poster.
        if upload.metadata.mime_type.startswith('video'):
            old_poster_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, thumbnail_directory, old_file_name + '.jpg')
            new_poster_thumbnail_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, poster_directory, thumbnail_directory, new_file_name + '.jpg')
            os.rename(old_poster_thumbnail_path, new_poster_thumbnail_path)

    old_exif_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, 'metadata', old_file_name + '.dat')
    new_exif_path = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO, 'metadata', new_file_name + '.dat')
    move_file(old_exif_path, new_exif_path)

    # Rename the file in Django's database.
    new_relative_path = os.path.join(upload_directory_name, new_file_name + extension).replace('\\','/') # This is the part of the path after /media/.
    upload.file.name = new_relative_path
    upload.relative_url = new_file_name.replace(" ","_")
    upload.save()
    upload.metadata.file_name = new_file_name
    upload.metadata.save()

# 3.1 Return the new name for the file.
def get_new_file_name(upload):
    hypothetical_file_name = upload.title
    # Remove characters that are unsupported in a common operating system or may lead to security vulnerabilities.
    hypothetical_file_name = get_valid_file_name(hypothetical_file_name)
    if hypothetical_file_name == '_':
        # get_valid_file_name() makes sure that the file name can't be an empty string by adding an underscore.
        # make_unique_with_random_id_suffix_within_character_limit() returns a random ID if passed an empty string. 
        # Reset the underscore to an empty string, with the effect of disallowing '_' as a file name.
        hypothetical_file_name = ''
    return make_unique_with_random_id_suffix_within_character_limit(hypothetical_file_name, 178, file_name_and_url_will_be_unique, upload)

# 4. After successfully processing the form, redirect to the homepage or the next page of the form if there is one.
# Input: upload_type, a string for the category. relative_url, a string which will be used when the upload is in the Pets category.
# In this case, the user doesn't need to fill out a second form, so the user will be redirected to the slide page for the new upload.
def redirect_to_next_page(upload_type, relative_url):
    if upload_type == 'adoption':
        return redirect('adoption_upload')
    elif upload_type == 'lost':
        return redirect('lost_upload')
    elif upload_type == 'found':
        return redirect('found_upload')
    else:
        return redirect('slide_page', relative_url)
