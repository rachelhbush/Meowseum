# file_validation_v0_0_0_5.py by Rachel Bush. Last modification: 
# PROGRAM ID: file_validation.py (_v0_0_0_5) / File validation
# REMARKS: This file contains the logic for validating an uploaded file while gathering its metadata.
# VERSION REMARKS: 

from django.conf import settings
import os
from Meowseum.file_handling.get_metadata import get_metadata
# These two import statements are for saving a temporary file.
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
# These four import statements are for delivering validation errors.
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDictKeyError
from django.template.defaultfilters import filesizeformat
from Meowseum.templatetags.my_filters import timeelapsed

# 0. By invoking this function in a view, you can validate a file and save the metadata generated while validating it.
# (In most other situations, the validator would be invoked in a class definition in a separate file.
# Invoking it in the view was the only way I could find to access the validator's return value.)
#
# Input: The name string for the file field, the form object, request.FILES, and the upload limits dictionary.
# Output: First, the metadata dictionary, except for the 'name' key, which Django may change during .save() as part of its built-in validation.
# If no file was uploaded, then return an empty string to store into the metadata variable in order to keep the logic the same. Second, the form.
def get_validated_metadata(field, form, request_files, validation_specifications):
    try:
        file = request_files[field]
        metadata = validate_file(file, validation_specifications)
    except ValidationError as error:
        form.add_error(field, error)
        metadata = ''
    except MultiValueDictKeyError as error:
        # When no file is uploaded, there is no key for the field in request.FILES, so trying to reference it causes an exception.
        # This is convenient, because we have to check for a file before trying to validate it.
        if form.fields[field].required:
            # Return an error if the field is required.
            if form.fields[field].error_messages['required'] == None:
                form.add_error('file', ValidationError("This field is required."))
            else:
                # Return the custom error message.
                form.add_error('file', ValidationError(form.fields[field].error_messages['required']))
        metadata = ''
    return metadata, form

# 1. This function contains the main logic for gathering the metadata from the file and validating it.
# Input: uploaded_file. The input file will be of the class InMemoryUploadedFile or TemporaryUploadedFile depending on the file size.
# validation_specifications, a dictionary with key-value pairs like 'max_fps', is specified in models.py. It will be used to further restrict whether the file will be
# accepted for processing.
def validate_file(uploaded_file, validation_specifications):
    temporary_file_path = temporarily_save_file(uploaded_file)
    metadata = get_metadata(uploaded_file, temporary_file_path)
    if not metadata['mime_type'] in settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS:
        default_storage.delete(temporary_file_path)
        raise ValidationError('Error: Unsupported file type.')
    temporary_file_path, uploaded_file, metadata = validate_extension(temporary_file_path, uploaded_file, metadata)
    # The remaining validation is specific to the field.
    if validation_specifications != None:
        if 'file_type' in validation_specifications:
            validate_file_type(metadata, validation_specifications['file_type'])
        if 'max_size' in validation_specifications:
            validate_size(temporary_file_path, metadata, validation_specifications['max_size'])
        if 'width' in metadata and 'height' in metadata:
            if 'exact_width' in validation_specifications and 'exact_height' in validation_specifications:
                if metadata['width'] != validation_specifications['exact_width'] or metadata['height'] != validation_specifications['exact_height']:
                    default_storage.delete(temporary_file_path)
                    raise ValidationError('Error: This field requires the file to be '+str(validation_specifications['exact_width'])+\
                                          'x'+str(validation_specifications['exact_height'])+'.') # e.g. This field requires the video to be 1920x1080.
            else:
                # If there is a key for both exact width and height, skip validating minimum dimensions and aspect ratio because it would be redundant.
                if 'exact_width' in validation_specifications and metadata['width'] != validation_specifications['exact_width']:
                    default_storage.delete(temporary_file_path)
                    raise ValidationError("Error: This field requires the file to be exactly "+str(validation_specifications['exact_width'])+" pixels wide.")
                else:
                    if 'exact_height' in validation_specifications and metadata['width'] != validation_specifications['exact_height']:
                        default_storage.delete(temporary_file_path)
                        raise ValidationError("Error: This field requires the file to be exactly "+str(validation_specifications['exact_height'])+" pixels tall.")
                if 'min_dimensions' in validation_specifications:
                    validate_minimum_dimensions(temporary_file_path, metadata, validation_specifications)
                if ('widest_aspect_ratio' in validation_specifications or 'narrowest_aspect_ratio' in validation_specifications or 'aspect_ratio' in validation_specifications):
                    validate_aspect_ratio(temporary_file_path, metadata, validation_specifications)
        if 'duration' in metadata:
            if 'max_duration' in validation_specifications and metadata['duration'] > validation_specifications['max_duration']:
                default_storage.delete(temporary_file_path)
                raise ValidationError('Error: The file is longer than ' + timeelapsed(validation_specifications['max_duration']) + '.' )
            else:
                if 'min_duration' in validation_specifications and metadata['duration'] < validation_specifications['min_duration']:
                    default_storage.delete(temporary_file_path)
                    raise ValidationError('Error: The file is shorter than the minimum' + timeelapsed(validation_specifications['min_duration']) + '.' )
        if 'fps' in metadata and 'max_fps' in validation_specifications and metadata['fps'] > validation_specifications['max_fps']:
            default_storage.delete(temporary_file_path)
            raise ValidationError('Error: The file has a frame rate higher than the maximum of' + validation_specifications['max_fps'] + '.')
    # Delete the temporary copy used during validation.
    default_storage.delete(temporary_file_path)
    return metadata

# 1.1 Django stores small files in memory, making them inaccessible to validation
# programs that require a string for a path. Temporarily save the file so
# that it can be validated.
# Input: uploaded_file. Output: The path to the temporarily saved file.
def temporarily_save_file(uploaded_file):
    # Retrieve an incomeplete path beginning with "../"
    temp_path = 'stage1_processing/%s' % uploaded_file.name
    # These two lines replace all Unicode characters in the file name with similar ASCII characters. The python-magic module, which determines the
    # MIME type, cannot read file names with certain characters that are not in the Windows-1252 character set when running on a Windows OS. This is
    # because python-magic is a wrapper around the C language (lets programmers use Python syntax with C language functions), and it's exceedingly
    # difficult to account for Unicode in both the Python and C versions. For example, the file name "Kočka_v_krmítku_2.jpg" led č and í being replaced
    # with \304 and \303, and Windows thinking that the \ meant a separate directory. I attempted to use .encode() to get a Unicode string to pass to
    # python-magic, but only got the error "'charmap' codec can't encode character '/u1010d' in position 97: character maps to <undefined>".
    # Renaming the temporary file is the simplest solution, and other than this situation, the file names fully support Unicode. 
    temp_path = str(temp_path.encode('ascii','ignore')) # For the given example file name, this returns "b'Koka_v_krmtku_2.jpg'".
    temp_path = temp_path[2:len(temp_path)-1]
    default_storage.save(temp_path, ContentFile(uploaded_file.file.read()))
    full_temp_path = os.path.join(settings.MEDIA_PATH, temp_path)
    return full_temp_path

# 1.2. First, standardize the extension to an all-lowercase version. Then, if the extension mismatches the type portion of the MIME type (e.g. a .jpg
# that is a video), then refuse the file. If the extension matches the type portion, then this may be a file type with multiple common extensions
# (e.g. .jpeg for .jpg) or the user may have made a mistake, so allow the file. The function will also rename the file as the standard extension for
# its type using what you specified in settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS, then update the metadata accordingly.
def validate_extension(temporary_file_path, uploaded_file, metadata):
    if not metadata['extension'].islower():
        # Standardize the extension to an all-lowercase version.
        temporary_file_path, uploaded_file, metadata = change_file_extension(temporary_file_path, uploaded_file, metadata, metadata['extension'].lower())

    type_portion = metadata['mime_type'].split('/')[0] # Get the type portion of the MIME type, e.g. image.
    if (type_portion == 'image' and metadata['extension'] not in settings.RECOGNIZED_IMAGE_EXTENSIONS) or (type_portion == 'video' and metadata['extension'] not in settings.RECOGNIZED_VIDEO_EXTENSIONS):
        default_storage.delete(temporary_file_path)
        # Because I am not sure whether it is wise to tell someone who definitely mislabeled the file that I'm suspicious of them,
        # I'm returning the same error message as when the file is unsupported.
        raise ValidationError('Error: Unsupported file type.')
    else:
        # If the MIME type isn't in the tuple of allowed MIME types for the file's extension, then rename the file.
        if metadata['mime_type'] not in get_corresponding_keys(settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS, metadata['extension']):
            # Find the extension matching the MIME type.
            preferred_extension = settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS[metadata['mime_type']]
            temporary_file_path, uploaded_file, metadata = change_file_extension(temporary_file_path, uploaded_file, metadata, preferred_extension)

    return temporary_file_path, uploaded_file, metadata

# 1.2.1. Each time the temporary file's extension is changed on the operating system, the temporary file path variable needs to change so the program
# will be able to delete the temporary file. The name of the InMemoryUploadedFile or TemporaryUploadedFile object needs to change so that it changes
# both the name of the permanent file and the name in the Django database. For the "name", it uses a path relative to the /media/ directory. The
# metadata dictionary needs to be updated.
# Input: temporary_file_path, uploaded_file (the InMemoryUploadedFile or TemporaryUploadedFile), metadata, new_extension
# Output: temporary_file_path, uploaded_file, metadata. The latter two are included for clarity, even though they are mutable.
def change_file_extension(temporary_file_path, uploaded_file, metadata, new_extension):
    extless_temporary_file_path = os.path.splitext(temporary_file_path)[0]
    extless_file_rel_path = os.path.splitext(uploaded_file.name)[0]
    metadata['extension'] = new_extension
    os.rename(temporary_file_path, extless_temporary_file_path + new_extension)
    temporary_file_path = extless_temporary_file_path + new_extension
    uploaded_file.name = extless_file_rel_path + new_extension
    return temporary_file_path, uploaded_file, metadata

# 1.2.2. Input: A dictionary with a one-to-many relationship between its keys and its values. A specific value from the dictionary.
# Output: A tuple of keys within the dictionary which correspond to the given value.
def get_corresponding_keys(dictionary, value):
    desired_keys = tuple()
    for key in dictionary:
        if dictionary[key] == value:
            desired_keys = desired_keys + (key,)
    return desired_keys

# 1.3. Validate the file's type using the 'file_type' list and the metadata keys 'motion_type' and 'mime_type'.
# Limiting the files only to those supported by the site as a whole is done separately by checking against the site settings in the main validation logic.
# By itself, when there are general arguments like 'video', this function lets any supported video through.
def validate_file_type(metadata, allowable_file_types):
    if metadata['motion_type'] in allowable_file_types:
        return
    elif 'gif-animated' in allowable_file_types and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video':
        return
    elif 'gif-still' in allowable_file_types and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image':
        return
    elif metadata['mime_type'] in allowable_file_types:
        return
    else:
        raise ValidationError('Error: Unsupported file type.')

# 1.5. Make sure the upload will not create too much work for the server before allowing it to be processed. Detect whether the upload is below
# a certain size for its file type.
def validate_size(temporary_file_path, metadata, max_size):
    if str(type(max_size)) == "<class 'dict'>":
        for entry in max_size:
            if entry == metadata['motion_type'] and metadata['file_size'] > max_size[entry]:
                raise_size_error(temporary_file_path, metadata, max_size[entry])
            elif entry == 'gif-still' and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image' and metadata['file_size'] > max_size[entry]:
                raise_size_error(temporary_file_path, metadata, max_size[entry])
            elif entry == 'gif-animated' and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video' and metadata['file_size'] > max_size[entry]:
                raise_size_error(temporary_file_path, metadata, max_size[entry])
            else:
                if entry == metadata['mime_type'] and metadata['file_size'] > max_size[entry]:
                    raise_size_error(temporary_file_path, metadata, max_size[entry])
    else:
        if metadata['file_size'] > max_size:
            raise_size_error(temporary_file_path, metadata, max_size)

# 1.5.1 Delete the file and return a size-related validation error.
def raise_size_error(temporary_file_path, metadata, max_size):
        default_storage.delete(temporary_file_path)
        raise ValidationError('Error: The '+metadata['motion_type']+' is larger than our processing limit of '+filesizeformat(max_size)+'.')

# 1.6. Make sure the upload is within constraints for minimum dimensions. This function contains the logic for finding the right constraint for the upload's file type
# -- only 'image' or 'video'.
def validate_minimum_dimensions(temporary_file_path, metadata, validation_specifications):
    if str(type(validation_specifications['min_dimensions'])) == "<class 'dict'>":
        for key in validation_specifications['min_dimensions']:
            if key == metadata['motion_type']:
                validate_minimum_dimensions_entry(temporary_file_path, metadata, validation_specifications['min_dimensions'][key])
    else:
        # The value should be a tuple.
        validate_minimum_dimensions_entry(temporary_file_path, metadata, validation_specifications['min_dimensions'])

# 1.6.1 This function contains the logic for checking an individual minimum dimensions constraint.
def validate_minimum_dimensions_entry(temporary_file_path, metadata, entry):
    if metadata['width'] < entry[0] and entry[1] == 0:
        default_storage.delete(temporary_file_path)
        raise ValidationError("Error: The "+metadata['motion_type']+" must be at least "+str(entry[0])+" pixels wide.")
    elif metadata['height'] < entry[1] and entry[0] == 0:
        default_storage.delete(temporary_file_path)
        raise ValidationError("Error: The "+metadata['motion_type']+" must be at least "+str(entry[1])+" pixels tall.")
    else:
        if metadata['width'] < entry[0] or metadata['height'] < entry[1]:
            default_storage.delete(temporary_file_path)
            raise ValidationError("Error: The "+metadata['motion_type']+" must be at least "+str(entry[0])+"x"+\
                                  str(entry[1])+".")

# 1.7. Make sure the upload is within constraints for the aspect ratio. First, check for the right constraint for the upload's file type.
def validate_aspect_ratio(temporary_file_path, metadata, validation_specifications):
    # The 'widest_aspect_ratio', 'narrowest_aspect_ratio', and 'aspect_ratio' keys all use the same if-block, but with slightly different functions.
    # Rather than use a higher-order function, I ohose to cut-and-paste the second block and change the variable names.
    if 'aspect_ratio' in validation_specifications:
        if str(type(validation_specifications['aspect_ratio'])) == "<class 'dict'>":
            # This constraint on aspect ratio is being limited to a certain file_type. Check if the file is any of those types before continuing.
            # By placing conditions for the most specific file_type keys at the top, limits for the more specific file_types will override those for more general ones.
            if 'gif-still' in validation_specifications['aspect_ratio'] and (metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image'):
                entry = validation_specifications['aspect_ratio']['gif-still']
            elif 'gif-animated' in validation_specifications['aspect_ratio'] and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video':
                entry = validation_specifications['aspect_ratio']['gif-animated']
            elif metadata['mime_type'] in validation_specifications['aspect_ratio']:
                entry = validation_specifications['aspect_ratio'][metadata['mime_type']]
            elif metadata['motion_type'] in validation_specifications['aspect_ratio']:
                entry = validation_specifications['aspect_ratio'][metadata['motion_type']]
            else:
                # The upload isn't one of the file types targeted by the constraint. Store an empty string in order to avoid referencing a variable with no value.
                entry = ''
            if entry != '':
                validate_aspect_ratio_entry(temporary_file_path, metadata, entry)
        else:
            validate_aspect_ratio_entry(temporary_file_path, metadata, validation_specifications['aspect_ratio'])
    else:
        if 'widest_aspect_ratio' in validation_specifications:
            if str(type(validation_specifications['widest_aspect_ratio'])) == "<class 'dict'>":
                # This constraint on aspect ratio is being limited to a certain file_type. Check if the file is any of those types before continuing.
                # By placing conditions for the most specific file_type keys at the top, limits for the more specific file_types will override those for more general ones.
                if 'gif-still' in validation_specifications['widest_aspect_ratio'] and (metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image'):
                    entry = validation_specifications['widest_aspect_ratio']['gif-still']
                elif 'gif-animated' in validation_specifications['widest_aspect_ratio'] and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video':
                    entry = validation_specifications['widest_aspect_ratio']['gif-animated']
                elif metadata['mime_type'] in validation_specifications['widest_aspect_ratio']:
                    entry = validation_specifications['widest_aspect_ratio'][metadata['mime_type']]
                elif metadata['motion_type'] in validation_specifications['widest_aspect_ratio']:
                    entry = validation_specifications['widest_aspect_ratio'][metadata['motion_type']]
                else:
                    # The upload isn't one of the file types targeted by the constraint. Store an empty string in order to avoid referencing a variable with no value.
                    entry = ''
                if entry != '':
                    validate_widest_aspect_ratio_entry(temporary_file_path, metadata, entry)
            else:
                validate_widest_aspect_ratio_entry(temporary_file_path, metadata, validation_specifications['widest_aspect_ratio'])
        if 'narrowest_aspect_ratio' in validation_specifications:
            if str(type(validation_specifications['narrowest_aspect_ratio'])) == "<class 'dict'>":
                # This constraint on aspect ratio is being limited to a certain file_type. Check if the file is any of those types before continuing.
                # By placing conditions for the most specific file_type keys at the top, limits for the more specific file_types will override those for more general ones.
                if 'gif-still' in validation_specifications['narrowest_aspect_ratio'] and (metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image'):
                    entry = validation_specifications['narrowest_aspect_ratio']['gif-still']
                elif 'gif-animated' in validation_specifications['narrowest_aspect_ratio'] and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video':
                    entry = validation_specifications['narrowest_aspect_ratio']['gif-animated']
                elif metadata['mime_type'] in validation_specifications['narrowest_aspect_ratio']:
                    entry = validation_specifications['narrowest_aspect_ratio'][metadata['mime_type']]
                elif metadata['motion_type'] in validation_specifications['narrowest_aspect_ratio']:
                    entry = validation_specifications['narrowest_aspect_ratio'][metadata['motion_type']]
                else:
                    # The upload isn't one of the file types targeted by the constraint. Store an empty string in order to avoid referencing a variable with no value
                    # in the next predicate.
                    entry = ''
                if entry != '':
                    validate_widest_aspect_ratio_entry(temporary_file_path, metadata, entry)
                validate_narrowest_aspect_ratio_entry(temporary_file_path, metadata, entry)
            else:
                validate_narrowest_aspect_ratio_entry(temporary_file_path, metadata, validation_specifications['narrowest_aspect_ratio'])
        
# 1.7.1. Check that the video stays narrower than an aspect ratio constraint, having been passed it as 'entry' by the parent function.
# This function is almost the same as the next one, except with changed variable names, conditions, and error messages.
# The main difference is that this one doesn't have an if-block account for 16:9 laptop resolutions, because 1360x768 is narrower than the 16:9 limit.
def validate_widest_aspect_ratio_entry(temporary_file_path, metadata, entry):
    if str(type(entry)) == "<class 'str'>":
        # Convert from a ratio in a string to a float.
        ratio_list = entry.split(':')
        widest_aspect_ratio = float(ratio_list[0]) / float(ratio_list[1])
        human_readble_widest_aspect_ratio = entry
    else:
        if str(type(entry)) == "<class 'int'>" or str(type(entry)) == "<class 'float'>":
            widest_aspect_ratio = entry
            human_readble_widest_aspect_ratio = format(widest_aspect_ratio,'.3f')+':1'
    if (metadata['width'] % widest_aspect_ratio > 10e-12 or metadata['width'] % 2 != 0 or metadata['height'] % 2 != 0)  and widest_aspect_ratio != 1:
        # If the height times the aspect ratio is exactly the width, as in 1920x1080, then width % aspect ratio will return a value smaller than 10^(-12) as a Python
        # rounding error.The rounding error will probably be between 0 and 4. Some applications require the width and the height to be even numbers, and sometimes
        # an even number is skipped. If 1:1 is specified, then rounding error isn't considered.
        critical_point = -4
    else:
        critical_point = 0
    # If the aspect ratio is wider than the limit, the left side will be a negative amount of pixels. For 1:1, 0.9*1-1 is negative.
    # So, the left side has to be more negative than the magnitude of the estimated possible rounding error to raise the validation error.
    if metadata['height'] * widest_aspect_ratio - metadata['width'] < critical_point:
        default_storage.delete(temporary_file_path)
        raise ValidationError("Error: The "+metadata['motion_type']+" has a wider aspect ratio than the limit of "+human_readble_widest_aspect_ratio+".")

# 1.7.2. Check that the video stays wider than an aspect ratio constraint, having been passed it as 'entry' by the parent function.
def validate_narrowest_aspect_ratio_entry(temporary_file_path, metadata, entry):
    if str(type(entry)) == "<class 'str'>":
        # Convert from a ratio in a string to a float.
        ratio_list = entry.split(':')
        narrowest_aspect_ratio = float(ratio_list[0]) / float(ratio_list[1])
        human_readble_narrowest_aspect_ratio = entry
    else:
        if str(type(entry)) == "<class 'int'>" or str(type(entry)) == "<class 'float'>":
            narrowest_aspect_ratio = entry
            human_readble_narrowest_aspect_ratio = format(narrowest_aspect_ratio,'.3f')+':1'
    if narrowest_aspect_ratio == 16/9 or human_readble_narrowest_aspect_ratio == '16:9' or human_readble_narrowest_aspect_ratio == '1.778:1':
        narrowest_aspect_ratio = 1360/768
    if (metadata['width'] % narrowest_aspect_ratio > 10e-12 or metadata['width'] % 2 != 0 or metadata['height'] % 2 != 0) and narrowest_aspect_ratio != 1:
        # If the height times the aspect ratio is exactly the width, as in 1920x1080, then width % aspect ratio will return a value smaller than 10^(-12) as a Python
        # rounding error. The rounding error will probably be between 0 and 4. Some applications require the width and the height to be even numbers, and sometimes
        # an even number is skipped. If 1:1 is specified, then rounding error isn't considered.
        critical_point = 4
    else:
        critical_point = 0
    # If the aspect ratio is narrower than the limit, the left side will be a positive amount of pixels. For 1:1, 1.1*1-1 is positive.
    # So, the left side has to be more positive than the magnitude of the estimated possible rounding error to raise the validation error.
    if metadata['height'] * narrowest_aspect_ratio - metadata['width'] > critical_point:
        default_storage.delete(temporary_file_path)
        raise ValidationError("Error: The "+metadata['motion_type']+" has a narrower aspect ratio than the limit of "+human_readble_narrowest_aspect_ratio+".")

# 1.7.3. Check that the video stays approximately at an aspect ratio constraint, having been passed it as 'entry' by the parent function.
# This is like the previous two functions, except using different conditions. 
def validate_aspect_ratio_entry(temporary_file_path, metadata, entry):
    if str(type(entry)) == "<class 'str'>":
        # Convert from a ratio in a string to a float.
        ratio_list = entry.split(':')
        allowable_aspect_ratio = float(ratio_list[0]) / float(ratio_list[1])
        human_readble_allowable_aspect_ratio = entry
    else:
        if str(type(entry)) == "<class 'int'>" or str(type(entry)) == "<class 'float'>":
            allowable_aspect_ratio = entry
            human_readble_allowable_aspect_ratio = format(allowable_aspect_ratio,'.3f')+':1'
    if allowable_aspect_ratio == 16/9 or human_readble_allowable_aspect_ratio == '16:9' or human_readble_allowable_aspect_ratio == '1.778:1':
        margin_of_error = 8
    elif (metadata['width'] % allowable_aspect_ratio > 10e-12 or metadata['width'] % 2 != 0 or metadata['height'] % 2 != 0) and allowable_aspect_ratio != 1:
        # If the height times the aspect ratio is exactly the width, as in 1920x1080, then width % aspect ratio will return a value smaller than 10^(-12) as a Python
        # rounding error. The rounding error will probably be between 0 and 4. Some applications require the width and the height to be even numbers, and sometimes
        # an even number is skipped. If 1:1 is specified, then rounding error isn't considered.
        margin_of_error = 4
    else:
        margin_of_error = 0
    # If the aspect ratio is wider than the error limit, the left side will be a negative amount of pixels.
    # If the aspect ratio is narrower than the error limit, the left side will be a positive amount of pixels.
    if metadata['height'] * allowable_aspect_ratio - metadata['width'] < -margin_of_error or metadata['height'] * allowable_aspect_ratio - metadata['width'] > margin_of_error:
        default_storage.delete(temporary_file_path)
        raise ValidationError("Error: The "+metadata['motion_type']+" must have an aspect ratio of "+human_readble_allowable_aspect_ratio+".")
