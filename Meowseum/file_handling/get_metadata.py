# get_metadata_v0_0_0_8.py by Rachel Bush. Last modification: 
# PROGRAM ID: get_metadata.py (_v0_0_0_8) / Get metadata
# REMARKS: This file contains the logic for gathering metadata from the file and storing it into a dictionary. This takes place
# during validation and initial processing. Then, the dictionary will have its information stored into the database.
# VERSION REMARKS: 

from django.conf import settings
import os
import magic
from PIL import Image, ImageSequence
import PIL.ExifTags
import json
from pymediainfo import MediaInfo
# Imports for _getexif()
import io
from PIL import TiffImagePlugin
from PIL.JpegImagePlugin import _fixup_dict

# 0. Create a dictionary, or JSON object, containing all information about the file that could be used while validating it. The dictionary will also
# contain any information to be used during compression, if it is convenient to obtain it now.
def get_metadata(uploaded_file, temporary_file_path):
    metadata = {}
    metadata['mime_type'] = get_mime_type(temporary_file_path)
    # Continue gathering metadata only if the site supports the MIME type.
    if metadata['mime_type'] in settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS:
        # Store the name of the file and extension separately. The Django file classes used when uploading have the .name attribute return the name+extension.
        # After the file is validated and stored, a different file class will have the .name attribute include the directory. So, the name and extension need
        # to be stored for consistency.
        split_name_list = os.path.splitext(uploaded_file.name)
        metadata['file_name'] = split_name_list[0]
        metadata['extension'] = split_name_list[1]
        # It is unavoidable that Django will rename the file when the record is saved, removing or replacing certain characters and adding a random ID suffix
        # if the name is taken. The original name and extension will be shown to the user during the upload process.
        # The remainder of this program works with the 'name' and 'extension' keys.
        metadata['original_file_name'] = metadata['file_name']
        metadata['original_extension'] = metadata['extension']
        metadata['file_size'] = uploaded_file.size
        
        if 'image' in metadata['mime_type']:
            metadata, number_of_frames = get_image_metadata(temporary_file_path, metadata)
        else:
            if 'video' in metadata['mime_type']:
                metadata = get_video_metadata(temporary_file_path, metadata)
        
        if metadata['mime_type'] != 'image/gif':
            # If the file isn't a .gif, store a placeholder value for the function which determines the motion type.
            number_of_frames = 'not a GIF'
        metadata['motion_type'] = get_motion_type(metadata, number_of_frames)
    return metadata

# 1. Return the MIME type for the file.
def get_mime_type(temporary_file_path):
    if os.name == 'nt':
        python_magic = magic.Magic(magic_file=settings.WINDOWS_MAGIC_PATH, mime=True)
    else:
        # On UNIX, the python_magic module is able to find the location of the data library automatically.
        python_magic = magic.Magic(mime=True)
    mime_type = python_magic.from_file(temporary_file_path)
    if mime_type == 'application/ogg' or mime_type=='application/octet-stream':
        mime_type = doubleCheckValidityWithMediaInfo(temporary_file_path, mime_type)
    return mime_type

# 1.1. Use the pymediainfo (MediaInfo) module to double-check the validity of the file. Sometimes python-magic returned the MIME type for unknown
# file types, 'application/octet-stream', despite having used a valid test file. This included .webm and .ogv files downloaded from Wikimedia Commons.
# It returned a MIME type for unknown file types, 'application/octet-stream'. python-magic also sometimes detected their files as application/ogg, for
# which .ogx is standard, but it was close enough I wanted to allow it. python-magic also had difficulty detecting valid .mkv (Matroska) files.
# Output: The true MIME type for the file, based on pymediainfo's judgment.
def doubleCheckValidityWithMediaInfo(temporary_file_path, mime_type):
    media_info = MediaInfo.parse(temporary_file_path)
    general_track = get_general_track(media_info)
    
    if 'internet_media_type' in general_track and 'video' in general_track['internet_media_type']:
        # Overwrite python_magic's MIME type conclusion with MediaInfo's conclusion. This worked to identify some video/webm and video/ogg files not identified by python-magic,
        # as well as .wmv files.
        mime_type = general_track['internet_media_type']
    else:
        if general_track['format'] == 'Matroska':
            if int(general_track['count_of_video_streams']) > 0:
                return 'video/x-matroska'
            else:
                if int(general_track['count_of_audio_streams']) > 0:
                    return 'audio/x-matroska'
    return mime_type

# 1.1.1. MediaInfo uses a list of tracks objects with track_type attributes, which can be General, Video, or Audio (also Chapters or Text for subtitles, but these aren't used).
# Videos have only one General track, which is for metadata that applies to all the video and audio streams as a whole.
# Input: media_info object. Output: The first track of the 'General' type, converted to a dictionary. 
def get_general_track(media_info):
    i=0
    while media_info.tracks[i].track_type != 'General':
        i+=1
    general_track = media_info.tracks[i].to_data()
    return general_track

# 2. Get all the information that is specific to an image or animated .gif file, using the Pillow module.
def get_image_metadata(temporary_file_path, metadata):
    image = Image.open(temporary_file_path)
    if metadata['mime_type'] == 'image/jpeg' and 'exif' in image.info:
        exif_data, metadata = get_exif_data(image.info['exif'], metadata)
    else:
        exif_data = None
    metadata = get_image_dimensions_and_orientation(image.size[0], image.size[1], metadata, exif_data)
    metadata, number_of_frames = get_animation_data(image, metadata)
    return metadata, number_of_frames

# 2.1. Given the raw EXIF data from the image, translate everything possible into human-readable form. Pillow is unable to translate the values from
# some tags, such as MakerNote or UserComment, which will still contain binary data. In addition to validation, I'll also use this function at some
# point after I store each JPEG's raw EXIF data in a separate file, when I extend EXIF querying functionality. Input: data, the EXIF data as a byte
# sequence. metadata dictionary. Output: A dictionary of EXIF data.
def get_exif_data(data, metadata):
    exif_data = {}
    for tag_id, value in _getexif(data).items():
        if tag_id in PIL.ExifTags.TAGS:
            tag_name = PIL.ExifTags.TAGS[tag_id]
            if str(type(value)) == "<class 'bytes'>":
                value = decode_exif_value(tag_name, value)
            exif_data[tag_name] = value

    if 'GPSInfo' in exif_data:
        raw_gps_info = exif_data['GPSInfo']
        gps_info = {}
        for tag_id, value in raw_gps_info.items():
            tag_name = PIL.ExifTags.GPSTAGS[tag_id]
            if tag_id in PIL.ExifTags.GPSTAGS:
                if str(type(value)) == "<class 'bytes'>":
                    value = decode_exif_value(tag_name, value)
                gps_info[tag_name] = value
        exif_data['GPSInfo'] = gps_info

    return exif_data, metadata

# 2.1.1. This is a modified version of a function in PIL.JpegImagePlugin. I changed it so that it accepts the raw data as the argument, rather than
# the Image object, so I can use it after retrieving raw EXIF data stored in a file.
# Input: data, the EXIF data as a byte sequence.
# Output: A dictionary of human-readable EXIF data, except the keys for EXIF tags use IDs corresponding to their names instead of their names.
def _getexif(data):
    # Extract EXIF information.  This method is highly experimental,
    # and is likely to be replaced with something better in a future
    # version.

    # The EXIF record consists of a TIFF file embedded in a JPEG
    # application marker (!).
    file = io.BytesIO(data[6:])
    head = file.read(8)
    # process dictionary
    info = TiffImagePlugin.ImageFileDirectory_v1(head)
    info.load(file)
    exif = dict(_fixup_dict(info))
    # get exif extension
    try:
        # exif field 0x8769 is an offset pointer to the location
        # of the nested embedded exif ifd.
        # It should be a long, but may be corrupted.
        file.seek(exif[0x8769])
    except (KeyError, TypeError):
        pass
    else:
        info = TiffImagePlugin.ImageFileDirectory_v1(head)
        info.load(file)
        exif.update(_fixup_dict(info))
    # get gpsinfo extension
    try:
        # exif field 0x8825 is an offset pointer to the location
        # of the nested embedded gps exif ifd.
        # It should be a long, but may be corrupted.
        file.seek(exif[0x8825])
    except (KeyError, TypeError):
        pass
    else:
        info = TiffImagePlugin.ImageFileDirectory_v1(head)
        info.load(file)
        exif[0x8825] = _fixup_dict(info)

    return exif

# 2.1.2. This function handles special decoding for certain EXIF tags. Pillow leaves the EXIF tags with an 'undefined' EXIF type as byte strings, even
# though they can be translated into character strings. Within these byte strings, sometimes Pillow has left hexidecimal values untranslated into
# decimal. This function re-encodes the byte string as UTF-8, the default for Python source code, and it replaces any ASCII characters from \x00 to
# \x09 with decimal digits. This function can't be applied to any EXIF tag, because there are tags like the UserComment tag and the MakerNote tag that
# will still contain raw binary, so an exception will occur if the function tries to decode them into a character string.
def decode_exif_value(tag_name, value):
    # EXIFVersion can have a value of b'0221' for version 2.21, and FlashPixVersion has the same problem.
    if tag_name in ['ExifVersion', 'FlashPixVersion', 'ComponentsConfiguration', 'GPSAltitudeRef', 'SceneType']:
        value = str(value, encoding='UTF-8')
        hexadecimal_characters_list = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08']
        decimal_characters_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
        for x in range(len(hexadecimal_characters_list)):
            value = value.replace(hexadecimal_characters_list[x], decimal_characters_list[x])
        if tag_name == 'GPSAltitudeRef' or tag_name == 'SceneType':
            # In the output for a test image's data, GPSAltitudeRef had a value of b'\x00', and the specification says this value should be an integer, usually 0 or 1.
            # To be consistent with other tags, all EXIF tags that use the 'undefined' type in the EXIF specification, yet can only have an integer value coded to some description,
            # will use the integer type.
            value = int(value)
    return value

# 2.2. Some cameras take photographs such that width is always the longest dimension, while storing the orientation of the camera. If necessary, this
# file handling package will losslessly rotate the image and reset the EXIF orientation to 1, because web browsers ignore the EXIF orientation. So,
# this function stores into 'original_exif_orientation' a number for the EXIF orientation, and it stores into 'width' and 'height' the value that will be used
# after losslessly rotating the image later.
# Input: file_width, file_height, exif_data dictionary, metadata dictionary
# Output: metadata dictionary with width, height, and possibly 'original_exif_orientation' keys added
def get_image_dimensions_and_orientation(file_width, file_height, metadata, exif_data=None):
    if exif_data != None and 'Orientation' in exif_data:
        metadata['original_exif_orientation'] = exif_data['Orientation']
        if metadata['original_exif_orientation'] <= 4:
            metadata['width'] = file_width
            metadata['height'] = file_height
        else:
            metadata['width'] = file_height
            metadata['height'] = file_width
    else:
        metadata['width'] = file_width
        metadata['height'] = file_height
    return metadata

# 2.3. Determine whether the image contains any animation. If it does, then store values for three of the keys that are also used for videos: duration, fps, and has_audio.
# Input: Image object, metadata dictionary. Output: metadata dictionary, number_of_frames
def get_animation_data(image, metadata):
    if metadata['mime_type'] == 'image/gif':
        number_of_frames = get_number_of_frames(image)
        if number_of_frames > 1:
            metadata['duration'] = get_gif_duration(image, number_of_frames)
            metadata['fps'] = number_of_frames / metadata['duration']
            metadata['has_audio'] = False
    else:
        # If the file isn't a .gif, store a placeholder value for the function which determines the human-readable type.
        number_of_frames = 'not a .gif'
    return metadata, number_of_frames

# 2.3.1. Input: A .GIF via an Image object from the Pillow module.
# Output: The number of frames in the GIF.
def get_number_of_frames(gif):
    frame=1 # Skip checking for a first frame at 0, because the GIF always contains at least one.
    try:
        while True:
            # Keep navigating the sequence of frames until an exception occurs.
            gif.seek(frame)
            frame+=1
    finally:
        return frame

# 2.3.2. Return the duration of the GIF in seconds by summing the duration of each frame.
# If the total duration is 0, then the author likely didn't care about the framerate or intended to
# defer to browser. Different browsers set the frame rate to 10fps when it is above a certain threshhold:
# 50fps for Chrome and Firefox and 16.67fps for IE7. If the total duration is 0, then this function
# assumes 10fps.
def get_gif_duration(gif, number_of_frames):
    gif_sequence = ImageSequence.Iterator(gif)
    gif_duration = 0
    for frame in gif_sequence:
        gif_duration += frame.info['duration']
    if gif_duration == 0:
        # For duration in seconds, return the number of frames divided by 10fps.
        return number_of_frames * 100
    else:
        # Convert from milliseconds to seconds.
        gif_duration /= 1000
        return gif_duration

# 3. Get all the information that is specific to a video file, using the MediaInfo module.
# A video file can have multiple video streams and multiple audio streams. This function assumes that all video streams will have the same width, height, and frame rate.
# Output via the metadata dictionary: 'width' and 'height' in pixels. 'duration' in seconds, 'fps', and 'has_audio'.
def get_video_metadata(temporary_file_path, metadata):
    media_info = MediaInfo.parse(temporary_file_path)
    general_track = get_general_track(media_info)
    first_video_track = get_first_video_track(media_info)

    metadata['has_audio'] = has_audio(media_info)
    metadata['width'], metadata['height'], metadata['needs_rotating'] = get_video_dimensions_and_orientation(first_video_track)
    metadata['duration'] = general_track['duration'] / 1000 # Convert duration from milliseconds to seconds.
    # The Windows version of MediaInfo located frame_rate and frame_count keys on the General track for an MP4 file, but on Debian 8, these keys were only located on a Video track.
    metadata['fps'] = float(first_video_track['frame_rate']) # MediaInfo stores frame_rate as a string.
    
    return metadata

# 3.1. Retrieve the first track of the Video type. Certain metadata, like the width and height of the video, are only present on video tracks.
# The program assumes these characteristics will be consistent for all videos.
# Input: media_info object. Output: The first track of the 'Video' type, converted to a dictionary. 
def get_first_video_track(media_info):
    i=0
    while media_info.tracks[i].track_type != 'Video':
        i+=1
    first_video_track = media_info.tracks[i].to_data()
    return first_video_track

# 3.2. Determine whether the video has audio by searching for an 'Audio' track.
# Input: media_info object. Output: True or False.
def has_audio(media_info):
    has_audio = False
    i=0
    while i < len(media_info.tracks):
        if media_info.tracks[i].track_type == 'Audio':
            has_audio = True
        i+=1
    return has_audio

# 3.3. Android and iOS devices record width as the longest dimension and height as the shortest dimension, regardless of whether or not the device
# is held horizontally or vertically. They record the way in which the device is rotated as 0, 90, 180, or 270. This function uses rotation
# information to obtain the video width as the horizontal dimension and the video height as the vertical dimension. It also returns True or False for
# whether the video needs to be rotated, because some Python programs used during processing can't handle video rotated 90 or 270 degrees.
# Input: first_video_track, a dictionary of information from the first video track. Output: width, height, and a needs_rotating Boolean
def get_video_dimensions_and_orientation(first_video_track):
    if 'rotation' in first_video_track:
        rotation = int(float(first_video_track['rotation']))
    else:
        rotation = 0
    width = first_video_track['width']
    height = first_video_track['height']
    if (rotation == 90 or rotation == 270 or rotation == -90) and width > height:
        needs_rotating = True
        width, height = height, width
    else:
        needs_rotating = False
    return width, height, needs_rotating

# 4. Classify the file as 'image', 'video', or 'file'. Files will be classified as video if they have motion.
# This allows a shorthand in validation_specifications or hosting_limits, the 'video' key, for indicating that the file should be validated for aspect ratio or duration,
# even if it is an animated .gif. For making decisions in the template, such as whether to use <img> or <video> for the file, look at only the mime_type instead.
# Modify this function when audio and documents are supported.
def get_motion_type(metadata, number_of_frames):
    if 'image' in metadata['mime_type'] and ((not metadata['mime_type'] == 'image/gif') or (metadata['mime_type'] == 'image/gif' and number_of_frames == 1)):
        type_name = 'image'
    elif 'video' in metadata['mime_type'] or (metadata['mime_type'] == 'image/gif' and number_of_frames > 1):
        type_name = 'video'
    else:
        type_name = 'file'
    return type_name
