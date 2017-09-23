# signals_v0_0_0_13.py by Rachel Bush. Date finished: 
# PROGRAM ID: signals.py (_v0_0_0_13) / Signals
# INSTALLATION: Python 3.5, Django 1.9.2
# REMARKS: This file is for altering the behavior of basic database actions, such as saving a record or deleting one, from the default.
# VERSION REMARKS: 

from Meowseum.models import Upload, Tag, hosting_limits_for_Upload
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from Meowseum.file_handling.file_utility_functions import remove_file

# When the last Upload record associated with a Tag record is deleted, delete the Tag record.
@receiver(pre_delete, sender=Upload)
# Use pre_delete in order to be able to access the record, because the upload will be removed from the relation's queryset immediately after being deleted.
def delete_tag_record_with_no_uploads(sender, **kwargs):
    for tag in kwargs['instance'].tags.all():
        if len(tag.uploads.all()) == 1:
            tag.delete()

# When an Upload record is deleted, then delete its file. Delete any existing thumbnail or poster files. This is necessary to prevent file naming conflicts with future uploads.
@receiver(pre_delete, sender=Upload)
def delete_upload_files(sender, instance, **kwargs):
    # Retrieve the values needed to assemble the path to the upload to be deleted and the paths to any existing associated files.
    file_database_value = instance.file.name
    file_directory, full_file_name = os.path.split(file_database_value)
    file_name, extension = os.path.splitext(full_file_name)
    thumbnail_directory = hosting_limits_for_Upload['thumbnail'][2]
    poster_directory = hosting_limits_for_Upload['poster_directory']

    # Assemble the paths to the upload and any existing associated files.
    file_path = os.path.join(settings.MEDIA_ROOT, file_directory, file_name) + extension
    thumbnail_path = os.path.join(settings.MEDIA_ROOT, file_directory, thumbnail_directory, file_name) + extension
    poster_path = os.path.join(settings.MEDIA_ROOT, file_directory, poster_directory, file_name) + '.jpg'
    poster_thumbnail_path = os.path.join(settings.MEDIA_ROOT, file_directory, poster_directory, thumbnail_directory, file_name) + '.jpg'
    exif_file_path = os.path.join(settings.MEDIA_ROOT, file_directory, 'metadata', file_name) + '.dat'

    # Delete the upload file any associated files.
    remove_file(file_path)
    remove_file(thumbnail_path)
    remove_file(poster_path)
    remove_file(poster_thumbnail_path)
    remove_file(exif_file_path)
