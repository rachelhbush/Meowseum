# Description: This form is for uploading a file from your PC or mobile device. Both the desktop and mobile versions present it in a modal.

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.models import TemporaryUpload, Upload, validation_specifications_for_Upload, hosting_limits_for_Upload, Metadata
from Meowseum.file_handling.file_validation import get_validated_metadata
from Meowseum.file_handling.stage2_processing import process_to_meet_hosting_limits
from Meowseum.forms import FromDeviceForm
import os
from django.conf import settings
from ipware.ip import get_real_ip
from Meowseum.file_handling.file_utility_functions import move_file, make_unique_with_random_id_suffix_within_character_limit, file_name_and_url_will_be_unique
from Meowseum.common_view_functions import ajaxWholePageRedirect

# 0. Main function
def page(request):
    # This is the outermost if-statement because a user shouldn't be accessing this page via AJAX unless the user is logged in.
    if request.user.is_authenticated():
        form = FromDeviceForm(request.POST or None, request.FILES or None)
        # If the user has submitted a form, begin validation.
        metadata, form = get_validated_metadata('file', form, request.FILES, validation_specifications_for_Upload)
        if form.is_valid():
            # Begin processing.
            temporary_upload, metadata = create_temporary_upload_record(form, metadata)
            new_upload, metadata = create_new_upload_record(temporary_upload, metadata, request)
            create_metadata_record(new_upload, metadata)
            # Redirect to the page for adding the title, description, and tags.
            return ajaxWholePageRedirect(request, reverse('upload_page1'))
        else:
            return render(request, 'en/public/upload_modal.html', {'from_device_form' : form})
    else:
        return ajaxWholePageRedirect(request, reverse('login'))
        
# 1. Create a temporary upload record. The TemporaryUpload model is used with a separate directory in case an exception occurs, including the server running
# out of memory. When this happens, the record and associated files can be deleted after the administrator examines what went wrong.
def create_temporary_upload_record(form, metadata):
    # If there weren't any validation errors, then begin creating a new TemporaryUpload record.
    temporary_upload = form.save()
    # Process the file.
    try:
        temporary_upload.file, metadata = process_to_meet_hosting_limits(temporary_upload.file, metadata, hosting_limits_for_Upload)
        temporary_upload.save()
        metadata = get_updated_file_name(temporary_upload, metadata)
    except Exception as e:
        temporary_upload.save()
        # Add the name of the file to the end of the exception message, so I can use it while investigating what went wrong.
        raise type(e)(str(e) + ". File path: " + temporary_upload.file.path).with_traceback(e.__traceback__)
    return temporary_upload, metadata

# 1.1. When a record with a file field is created, Django may remove or replace certain characters as part of its built-in validation.
# Update the metadata dictionary after the upload record is intially saved.
# Input: temporary_upload, the upload record. metadata, the metadata dictionary
# Output: The metadata dictionary with the 'name' field appropriately modified.
def get_updated_file_name(temporary_upload, metadata):
    full_file_name = temporary_upload.file.name.split('/')[1] # Discard the directory part of the database value.
    file_name = os.path.splitext(full_file_name)[0]
    metadata['file_name'] = file_name
    return metadata

# 2. File processing was successful, so copy the TemporaryUpload record to the table for Upload records and move the associated files.
def create_new_upload_record(temporary_upload, metadata, request):
    source_directory = os.path.join(settings.MEDIA_PATH, TemporaryUpload.UPLOAD_TO)
    destination_directory = os.path.join(settings.MEDIA_PATH, Upload.UPLOAD_TO)
    old_full_file_name = metadata['file_name'] + metadata['extension']
    old_exif_file_name = metadata['file_name'] + '.dat'
    old_poster_file_name = metadata['file_name'] + '.jpg'
    source_path = os.path.join(source_directory, old_full_file_name)
    thumbnail_directory_name = hosting_limits_for_Upload['thumbnail'][2]
    poster_directory_name = hosting_limits_for_Upload['poster_directory']
    # Make sure the file name is unique, in case the file name is already taken, and overwrite the new name into the metadata dictionary.
    metadata['file_name'] = make_unique_with_random_id_suffix_within_character_limit(metadata['file_name'], 178, file_name_and_url_will_be_unique)
    new_full_file_name = metadata['file_name'] + metadata['extension']
    new_exif_file_name = metadata['file_name'] + '.dat'
    new_poster_file_name = metadata['file_name'] + '.jpg'
    destination_path = os.path.join(destination_directory, new_full_file_name)
    # This will be the value associated with the main file in the database, a location relative to the /media/ directory.
    destination_relative_path = Upload.UPLOAD_TO + '/' + new_full_file_name

    # Move the file to the long-term upload directory.
    os.rename(source_path, destination_path)
    # Copy the file name with spaces replaced with underscores to the upload's URL.
    new_upload = Upload(file=destination_relative_path, relative_url=metadata['file_name'].replace(" ","_"))
    new_upload = get_user_information(new_upload, request) 
    new_upload.save()
    
    # Move all the upload's associated files, like the thumbnail and the poster image for <video>s, to the main directories.
    exif_source_path = os.path.join(source_directory, 'metadata', old_exif_file_name)
    exif_destination_path = os.path.join(destination_directory, 'metadata', new_exif_file_name)
    move_file(exif_source_path, exif_destination_path)
    thumbnail_source_path = os.path.join(source_directory, thumbnail_directory_name, old_full_file_name)
    thumbnail_destination_path = os.path.join(destination_directory, thumbnail_directory_name, new_full_file_name)
    move_file(thumbnail_source_path, thumbnail_destination_path)
    poster_source_path = os.path.join(source_directory, poster_directory_name, old_poster_file_name)
    poster_destination_path = os.path.join(destination_directory, poster_directory_name, new_poster_file_name)
    move_file(poster_source_path, poster_destination_path)
    poster_thumbnail_source_path = os.path.join(source_directory, poster_directory_name, thumbnail_directory_name, old_poster_file_name)
    poster_thumbnail_destination_path = os.path.join(destination_directory, poster_directory_name, thumbnail_directory_name, new_poster_file_name)
    move_file(poster_thumbnail_source_path, poster_thumbnail_destination_path)
    temporary_upload.delete()
    return new_upload, metadata

# 2.1. Retrieve information related to the identity of the uploader.
def get_user_information(new_upload, request):
    # Store the IP address of the uploader.
    ip_address = get_real_ip(request)
    if ip_address is not None:
        new_upload.uploader_ip = get_real_ip(request)
    # If the user is logged in, store the account information.
    if request.user.is_authenticated():
        new_upload.uploader = request.user
    return new_upload

# 3. Create and save a metadata record for a new upload record that is an image or video.
# Input: new_upload record, metadata dictionary. Output: None.
def create_metadata_record(new_upload, metadata):
    new_record = Metadata(upload=new_upload)
    # This is a list of the keys within the metadata dictionary which correspond to Metadata fields, so their values will be saved to the database.
    list_of_field_names = ['file_name', 'extension', 'original_file_name', 'original_extension', 'mime_type', 'file_size', 'width', 'height', 'duration', 'fps', 'has_audio', 'original_exif_orientation']
    for field in list_of_field_names:
        if field in metadata:
            # exec() is safe to use here because user input isn't involved in determining the characters within the string sent to the interpreter for execution.
            exec("new_record." + field + " = metadata['" + field + "']")
    new_record.save()
