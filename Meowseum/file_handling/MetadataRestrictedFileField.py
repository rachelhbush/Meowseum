# Description: MetadataRestrictedFileField, for models.py, allows restricting accepted files by type and metadata.
# If you want to retain metadata after uploading, in the view that handles the uploaded file, you will need to invoke get_validated_metadata().
# After the file is validated and the record is saved, pass the record to the other main function, process_to_meet_hosting_limits().
# Read the comments on the field and the two main functions.

from django.db.models import FileField
from django import forms
from django.conf import settings

class MetadataRestrictedFileField(FileField):
    def __init__(self, *args, **kwargs):
        self.validation_specifications = kwargs.pop("validation_specifications", None)
        super(MetadataRestrictedFileField, self).__init__(*args, **kwargs)
    def formfield(self, *args, **kwargs):
        defaults = {'form_class': forms.FileField}
        # When the field doesn't specify a file type restriction, all files show up in the file picker.
        if self.validation_specifications != None and 'file_type' in self.validation_specifications:
            defaults['widget'] = forms.widgets.FileInput(attrs= {'accept' : self.get_accept_value(self.validation_specifications['file_type']) } )
        defaults.update(kwargs)
        return super(MetadataRestrictedFileField, self).formfield(**defaults)
    # Input: validation_specifications['file_type']. Output: The function returns a string for the value of the accept attribute to formfield.
    def get_accept_value(self, allowable_file_types):
        accept_value_list = []
        for i in range(len(allowable_file_types)):
            if allowable_file_types[i] == 'all':
                for j in range(len(settings.CONVERTIBLE_IMAGE_TYPES)):
                    if settings.CONVERTIBLE_IMAGE_TYPES[j] not in accept_value_list: # This predicate prevents 'image/gif' from being included multiple times.
                        accept_value_list = accept_value_list + [settings.CONVERTIBLE_IMAGE_TYPES[j]]
                for j in range(len(settings.CONVERTIBLE_VIDEO_TYPES)):
                    if settings.CONVERTIBLE_VIDEO_TYPES[j] not in accept_value_list:
                        accept_value_list = accept_value_list + [settings.CONVERTIBLE_VIDEO_TYPES[j]]
            elif allowable_file_types[i] == 'image':
                for j in range(len(settings.CONVERTIBLE_IMAGE_TYPES)):
                    if settings.CONVERTIBLE_IMAGE_TYPES[j] not in accept_value_list:
                        accept_value_list = accept_value_list + [settings.CONVERTIBLE_IMAGE_TYPES[j]]
            elif allowable_file_types[i] == 'video':
                for j in range(len(settings.CONVERTIBLE_VIDEO_TYPES)):
                    if settings.CONVERTIBLE_VIDEO_TYPES[j] not in accept_value_list:
                        accept_value_list = accept_value_list + [settings.CONVERTIBLE_VIDEO_TYPES[j]]
            elif allowable_file_types[i] == 'gif-still' or allowable_file_types[i] == 'gif-animated':
                if 'image/gif' not in accept_value_list:
                    accept_value_list = accept_value_list + ['image/gif']
            else:
                if allowable_file_types[i] not in accept_value_list: # This predicate makes sure each MIME type is unique.
                    accept_value_list = accept_value_list + [allowable_file_types[i]]
        if 'video/ogg' in accept_value_list:
            # Sometimes video files using Ogg codecs use a general container for the Ogg format, instead of the one specific to video. This causes python-magic
            # but not MediaInfo to detect the file as 'application/ogg'. I account for that during validation. Here, though, I want application/ogg to also be
            # shown in the file picker if video/ogg is shown in the file picker, in case Windows does the same thing as python-magic.
            accept_value_list = accept_value_list + ['application/ogg']
        accept_value_string = ', '.join(accept_value_list)
        return accept_value_string
