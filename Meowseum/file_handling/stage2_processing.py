# Description: Process a validated file to meet hosting limits. These are limits for a file the user hasn't edited through cropping, clipping, etc.

from django.conf import settings
from Meowseum.models import TemporaryUpload
import os
from PIL import Image
from moviepy.editor import VideoFileClip
import moviepy.video.fx.resize
from moviepy.config_defaults import FFMPEG_BINARY, IMAGEMAGICK_BINARY
from math import ceil
import subprocess
from qtfaststart.processor import process as qtfaststart
from Meowseum.file_handling.get_metadata import get_exif_data

# 0. Convert the file, scale it down, and do other operations to put it within the constraints specified by the arguments supplied by the hosting_limits dictionary.
# Input: 1. The 'file' argument now uses the class 'django.db.models.fields.files.FieldFile'.
# It doesn't say this in the documentation, but it has a file.path attribute that is read-only.
# You can still change it indirectly by using file.name, but now the attribute includes the directory path relative to \media\ instead of just the file name and extension.
# 2. The metadata dictionary.
# 3. The hosting_limits dictionary.
# Output: The updated file and metadata.
def process_to_meet_hosting_limits(file, metadata, hosting_limits):
    # Validate the view's input to determine whether the view is written correctly. Deliver warnings to the Django programmer.
    if file == None:
        exception = RuntimeErrror("'None' was passed to process_to_meet_hosting_limits(). If the file is optional, check that your view has an 'if record.file != None' predicate for handling\
the possibility that the user chose not to upload anything. If the file is required, check that the <form> has enctype='multipart/form-data' set.")
        raise exception
    
    # Use the metadata to determine how to interpret hosting_limits and calculate processing variables that apply specifically to the user's file.
    save_type_list, new_dimensions, gif_dimensions, output_bitrate, needs_bitrate_lowering = determine_output_parameters(file, metadata, hosting_limits)                
    # Begin processing the file. These functions include checking whether any re-encoding actually needs to be done, so the file may be returned unchanged.
    if metadata['motion_type'] == 'image':
        file, metadata = process_image(file, metadata, hosting_limits, save_type_list, new_dimensions)
    else:
        if metadata['motion_type'] == 'video':
            file, metadata = process_video(file, metadata, hosting_limits, save_type_list, new_dimensions, gif_dimensions, output_bitrate, needs_bitrate_lowering)
            
    if 'thumbnail' in hosting_limits:
        if (hosting_limits['thumbnail'][0] == 'width' and metadata['width'] > hosting_limits['thumbnail'][1]) or (hosting_limits['thumbnail'][0] == 'height' and metadata['height'] > hosting_limits['thumbnail'][1]):
            if 'image' in metadata['mime_type']:
                create_image_thumbnail(file, metadata, hosting_limits)
            else:
                create_video_thumbnail(file, metadata, hosting_limits)

    return file, metadata

# 1. Take the arguments given to the field and determine how they apply to the specific file that the user is uploading.
# This function calculates the parameters with which the file will be processed.
# Output: save_type_list, new_dimensions, new_bitrate, needs_bitrate_lowering
def determine_output_parameters(file, metadata, hosting_limits):
    # For the first three variables, 'None' serves to indicate that the file doesn't need to be processed for this quality.
    # For the fourth, it is a placeholder for when the file isn't a video, and the decision-making is done with a separate Boolean variable.
    save_type_list, new_dimensions, gif_dimensions, output_bitrate, needs_bitrate_lowering = None, None, None, None, False
    if 'conversion' in hosting_limits:
        save_type_list = get_save_type(metadata, hosting_limits['conversion'])
    if 'max_dimensions' in hosting_limits:
        new_dimensions, gif_dimensions = get_new_dimensions(metadata, hosting_limits['max_dimensions'], save_type_list)
    if metadata['mime_type'].startswith('video'):
        output_bitrate, needs_bitrate_lowering = get_output_bitrate(metadata, hosting_limits, new_dimensions)
    return save_type_list, new_dimensions, gif_dimensions, output_bitrate, needs_bitrate_lowering

# 1.1 Determine which file extension(s) will be used for saving the file at the end of the main function.
# File extensions are used instead of MIME types because they are used by the Pillow and MoviePy for saving.
# Input: metadata, the 'conversion' argument's 2D-tuple
# Output: list of MIME types. Return 'None' if the file doesn't need converting.
def get_save_type(metadata, conversion_information):
    conversion_info = filter_conversion_tuples_by_size_criterion(conversion_information, metadata)

    from_list = []
    for x in range(len(conversion_info)):
        from_list = from_list + [conversion_info[x][0]]
    # Find the most specific matching "from" entry in the inner tuple.
    # This "most specific type" problem previously occurred in the aspect ratio function, so I reused its if-elif-else structure.
    if 'gif-still' in from_list and (metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image'):
        convert_from = 'gif-still'
    elif 'gif-animated' in from_list and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video':
        convert_from = 'gif-animated'
    elif metadata['mime_type'] in from_list:
        convert_from = metadata['mime_type']
    elif metadata['motion_type'] in from_list:
        convert_from = metadata['motion_type']
    else:
        # The upload isn't one of the file types targeted by the constraint.
        return None
    for x in range(len(conversion_info)):
        if conversion_info[x][0] == convert_from:
            # If the first entry of the current tuple is the most specific "from" entry, then this is the desired tuple for converting.
            converting_tuple = conversion_info[x]

    # If the tuple doesn't have a "to" type, or the "from" entry and the only "to" entry are the same, or the only "to" category is a subcategory of the "from" category, return an empty list.
    # The tuple is only being used to exempt the file from following a rule for converting from a general type like "image", and no conversion operations will be done with the file.
    # In other words, this is the part of the function that implements the "exempt from the general rule" feature of the conversion argument.
    # The second part of this predicate makes it ignore the last entry of the tuple if it contains a file size threshhold.
    if len(converting_tuple) == 1 or (len(converting_tuple) == 2 and str(type(converting_tuple[1])) == "<class 'int'>"):
        return None
    else:
        if len(converting_tuple) == 2 or (len(converting_tuple) == 3 and str(type(converting_tuple[2])) == "<class 'int'>"):
            if converting_tuple[1] == converting_tuple[0] or converting_tuple[1] == metadata['mime_type']:
                return None

    # Store all string entries of converting_tuple after the first entry, the 'from' entry. This skips over the numerical entry which represents the file size threshhold.
    save_type_list = []
    for x in range(1, len(converting_tuple)):
        if str(type(converting_tuple[x])) == "<class 'str'>":
            save_type_list = save_type_list + [converting_tuple[x]]
    return save_type_list

# 1.1.1. Filter conversion rule tuples down to only those without a size criterion or with a size criterion that the file's size meets.
# Input: conversion_information, the 2D tuple containing all the tuples representing conversion rules. metadata dictionary for the file.
# Output: conversion_info, a 2D list containing only tuples relevant to the file's size.
def filter_conversion_tuples_by_size_criterion(conversion_information, metadata):
    # Use a list comprehension instead of iterating over it using indices, because the indices would change while removing items from the list.
    conversion_info = [rule for rule in conversion_information if is_relevant_to_file_size(rule, metadata)]
    return conversion_info

# 1.1.1.1. Input: A tuple representing a rule for converting a file.
# Output: True or False depending on whether or not the tuple is relevant to the file, considering its size criterion
def is_relevant_to_file_size(conversion_rule, metadata):
    # The tuple has a size criterion if its last entry is an integer.
    if str(type( conversion_rule[len(conversion_rule)-1] )) == "<class 'int'>":
        if len(conversion_rule) == 2 or (len(conversion_rule) == 3 and str(type(conversion_rule[2])) == "<class 'int'>"):
            # The tuple is for exempting the file format from a more general rule, such as exempting GIFs under 1MB from being converted to MP4,
            # so the tuple is relevant if the file is under the size limit.
            if metadata['file_size'] <= conversion_rule[len(conversion_rule)-1]:
                return True
            else:
                return False
        else:
            # The tuple is a normal case. The tuple is relevant if the file is over or equal to the size limit so the file will be converted using it.
            if metadata['file_size'] >= conversion_info[x][len(conversion_info[x])-1]:
                return True
            else:
                return False
    else:
        return True

# 1.2. Calculate the dimensions of the file needed for it to stay within the limits while maintaining aspect ratio. This function can be used with
# both images and videos. First, determine which the maximum dimension constraint applies to the file's type.
# Input: metadata dictionary. max_dimensions takes the form (1920, 1200) or ((1920, 1200), (1080, 1920)) or {'image': ((1920, 1200), (1080, 1920))}.
# save_type_list of MIME types being converted toward.
# Output: The function returns two values. The first value is a (width, height) tuple, or None if the file doesn't need to be resized.
# The second value is also a (width, height) tuple, but for the video's size after converting to .gif. It returns None if separate .gif dimensions
# are not needed.
def get_new_dimensions(metadata, max_dimensions, save_type_list):
    if str(type(max_dimensions)) == "<class 'dict'>":
        # Generate a set of keys in the type dictionary and choose the most specific one matching the file.
        type_keys = max_dimensions.keys()
        if 'gif-still' in type_keys and (metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'image'):
            file_type = 'gif-still'
        elif 'gif-animated' in type_keys and metadata['mime_type'] == 'image/gif' and metadata['motion_type'] == 'video':
            file_type = 'gif-animated'
        elif metadata['mime_type'] in type_keys:
            file_type = metadata['mime_type']
        elif metadata['motion_type'] in type_keys:
            file_type = metadata['motion_type']
        else:
            # The upload isn't one of the file types targeted by the constraint.
            file_type, file_dimensions = None, None

        if file_type != None:
            file_dimensions = process_L_shaped_constraint(metadata['width'], metadata['height'], max_dimensions[file_type])
        # If the program is converting to .gif, and .gif uses separate dimension constraints, then the function will be returning the dimensions for the .gif.
        gif_dimensions = None
        if save_type_list != None and metadata['mime_type'] != 'image/gif' and 'image/gif' in save_type_list:
            if 'image/gif' in max_dimensions:
                gif_dimensions = process_L_shaped_constraint(metadata['width'], metadata['height'], max_dimensions['image/gif'])
            else:
                if 'gif-animated' in max_dimensions:
                    gif_dimensions = process_L_shaped_constraint(metadata['width'], metadata['height'], max_dimensions['gif-animated'])
        return file_dimensions, gif_dimensions
        
    else:
        return process_L_shaped_constraint(metadata['width'], metadata['height'], max_dimensions), None

# 1.2.1 This function examines a constraint on the image size. In the first case, the constraint looks like (1920, 1200) and in the second, it looks like
# ((1920, 1200), (1080, 1920)), a 2D tuple with a landscape constraint and a portrait constraint. The first boundary is rectangular, and the second is L-shaped
# with the image at the intersection of the L. This function determines which rectangle allows the largest fitting image.
def process_L_shaped_constraint(width, height, max_dimensions):
    if str(type(max_dimensions)) == "<class 'tuple'>" and str(type(max_dimensions[0])) == "<class 'int'>":
        return process_rectangular_constraint(width, height, max_dimensions[0], max_dimensions[1])
    elif str(type(max_dimensions)) == "<class 'tuple'>" and str(type(max_dimensions[0])) == "<class 'tuple'>":
        # Pick the inner tuple with the largest proportion between the shrunk image and the original image.
        ratio1 = min(max_dimensions[0][0] / width , max_dimensions[0][1] / height)
        ratio2 = min(max_dimensions[1][0] / width , max_dimensions[1][1] / height)
        if ratio1 > ratio2:
            return process_rectangular_constraint(width, height, max_dimensions[0][0], max_dimensions[0][1])
        else:
            return process_rectangular_constraint(width, height, max_dimensions[1][0], max_dimensions[1][1])

# 1.2.1.1 This function examines an individual rectangular boundary for shrinking the image or video. The parent functions determine which boundary
# for the should be passed.
# Input: The width of the file, the height of the file, and the boundary width, and the boundary height.
# Output: A (width, height) tuple for the shrunk image or video.
def process_rectangular_constraint(file_width, file_height, boundary_width, boundary_height):
    if file_width <= boundary_width and file_height <= boundary_height:
        return None
    # This predicate determines which of the dimensions is the limiting factor. The shrunk file will have a pair of edges touching the boundary.
    # The limiting dimension is whichever one has the larger Image:Boundary ratio. Restated, it is the one with the smaller Boundary:Image ratio.
    # For this problem, it helped to consider examples and sketch them out.
    # A (600, 600) image shrunk to be within (500, 300) will be (300, 300).
    # A (600, 500) image shrunk to be within (500, 300) will be (360, 300). In both cases, the limiting dimension is height.
    elif boundary_width / file_width < boundary_height / file_height:
        new_width = boundary_width
        new_height = round( file_height * (boundary_width / file_width) ) # Shrink height by the same proportion.
        return (new_width, new_height)
    else:
        new_height = boundary_height
        new_width = round( file_width * (boundary_height / file_height) ) # Shrink width by the same proportion.
        return (new_width, new_height)

# 1.3. If the bitrate is deemed excessive, or the file is being resized, return the new bitrate in bits/second. If it isn't, return the current bitrate.
# The function determines whether the bitrate will exceed the maximum, both absolute and for its dimensions using the Power of 0.75 formula.
# Output: A string such as '53k', for 53 kbps. MoviePy requires bitrate to be in this format. It also returns a Boolean that flips to True when
# the bitrate needs to be lowered. This is useful when lowering the bitrate may be the only reason to re-encode the video and you want to avoid it when you can.
# To retrieve only the output bitrate, use [0] after the function call to get only the string.
def get_output_bitrate(metadata, hosting_limits, new_dimensions):
    bitrate = metadata['file_size']*8 / metadata['duration'] # Convert bytes to bits and divide by the number of seconds.
    needs_bitrate_lowering = False
    if new_dimensions == None:
        width = metadata['width']
        height = metadata['height']
    else:
        # The file is being resized. A bitrate must be specified in order for MoviePy to treat the different codecs consistently. So, use the Power of 0.75
        # formula to find the new bitrate for resizing the file.
        bitrate = ((new_dimensions[0] * new_dimensions[1]) / (metadata['width'] * metadata['height'])) ** 0.75 * bitrate
        needs_bitrate_lowering = True
        # Setting up the variables this way will allow a file that will be resized to be handled the same way as a file that won't be resized.
        width, height = new_dimensions[0], new_dimensions[1]
        
    # Determine the bitrate cap based on frame area and fps. In case there is no cap, use a None placeholder.
    max_bitrate = None
    if 'power_formula_coordinate' in hosting_limits:
        max_bitrate = ((width * height) / (hosting_limits['power_formula_coordinate'][1]**2 * (16/9))) ** 0.75 \
                      * hosting_limits['power_formula_coordinate'][0]
    if 'max_bitrate' in hosting_limits and hosting_limits['max_bitrate'] > max_bitrate:
        # If the absolute bitrate cap is more stringent than the cap from the Power of 0.75 formula, then use the absolute bitrate cap.
        max_bitrate = hosting_limits['max_bitrate']
    if 'high_fps_multiplier' in hosting_limits and metadata['fps'] > 48:
        max_bitrate *= hosting_limits['high_fps_multiplier']

    if max_bitrate == None or bitrate < max_bitrate:
        new_bitrate = bitrate # Keep the current bitrate or calculated bitrate for the resized file.
    else:
        if bitrate > max_bitrate:
            # Use the most stringent bitrate cap.
            new_bitrate = max_bitrate
            needs_bitrate_lowering = True
            if 'reencode_multiplier' in hosting_limits and new_dimensions == None:
                new_bitrate *= hosting_limits['reencode_multiplier']
    # Convert to MoviePy's preferred format. Round upward to the nearest kbps so that a file will never use 0 kbps.
    new_bitrate = str(ceil(new_bitrate / 1000))+'k'
    return new_bitrate, needs_bitrate_lowering

# 2. Use Pillow to process the image file. Return the updated file and metadata.
def process_image(file, metadata, hosting_limits, save_type_list, new_dimensions):
    autorotate_image(file.path, metadata, hosting_limits)
    separate_exif_data_from_file(file.path, metadata['mime_type'])
    
    image = Image.open(file.path)
    if new_dimensions != None:
        # Shrink the image.
        image.thumbnail(new_dimensions)
        metadata['width'] = new_dimensions[0]
        metadata['height'] = new_dimensions[1]
        if save_type_list == None:
            # This was the only task.
            save_image(image, file.path, hosting_limits, metadata['mime_type'])
            del image
            image = Image.open(file.path)
            metadata['file_size'] = file.size
    if save_type_list != None:
        # Obtain the file path without the extension on the end, as well as the current extension.
        extless_file_path, old_ext = os.path.splitext(file.path)
        old_ext = old_ext.lower()
        # Obtain the path relative to \media\ without the extension on the end.
        extless_file_rel_path = os.path.splitext(file.name)[0]
        for x in range(len(save_type_list)):
            # Convert the file using each extension in the list. Unless there were changes, skip saving as the original extension.
            if settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS[save_type_list[x]] != old_ext or new_dimensions != None:
                save_image(image, extless_file_path + settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS[save_type_list[x]], hosting_limits, metadata['mime_type'])
        del image # Close the original file so that, if it isn't needed, it can be deleted.
        file, metadata = post_conversion_update(file, metadata, save_type_list, extless_file_path, extless_file_rel_path, old_ext)
    return file, metadata

# 2.1. This function checks if the image needs rotating and/or mirroring, based on the image's EXIF orientation data, before web browsers will display
# it correctly. If it does, the function use the command line tool JHEAD to losslessly adjust the image, then it changes the image's EXIF orientation to 1.
def autorotate_image(file_path, metadata, hosting_limits):
    if 'original_exif_orientation' in metadata and metadata['original_exif_orientation'] > 1 and metadata['original_exif_orientation'] < 9:
        if 'jpeg_quality' in hosting_limits:
            jpeg_quality = str(hosting_limits['jpeg_quality'])
        else:
            jpeg_quality = '75'
        if os.name == 'nt':
            command = [IMAGEMAGICK_BINARY, file_path, '-auto-orient', '-quality', jpeg_quality, file_path]
        else:
            # The UNIX installation allows using the 'convert' command instead of the path to the executable.
            command = ['convert', file_path, '-auto-orient', '-quality', jpeg_quality, file_path]
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            raise IOError(e.output)

# 2.2. If the file is a JPEG with EXIF data, store the EXIF data. Then, for privacy purposes, remove the EXIF data from the JPEG itself using the JHEAD command line tool.
def separate_exif_data_from_file(file_path, mime_type):
    image = Image.open(file_path)
    if mime_type == 'image/jpeg' and 'exif' in image.info:
        store_raw_exif_data(file_path, image)
        remove_exif_data_from_file(file_path)
    del image

# 2.2.1. Store the EXIF data into a separate file.
def store_raw_exif_data(file_path, image):
    raw_exif_data = image.info['exif']
    full_file_name = os.path.split(file_path)[1]
    file_name = os.path.splitext(full_file_name)[0]
    exif_data_file_path = os.path.join(settings.MEDIA_PATH, TemporaryUpload.UPLOAD_TO, 'metadata', file_name + '.dat')
    outfile = open(exif_data_file_path, 'wb')
    outfile.write(raw_exif_data)
    outfile.close()

# 2.2.2. Remove the EXIF data from the JPEG.
def remove_exif_data_from_file(file_path):
    command = [settings.JHEAD_PATH, '-de', file_path]
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        raise IOError(e.output)

# 2.3 Save an image. If the file is a JPEG and the programmer specified a JPEG quality setting, the function uses it.
# When converting from a PNG with transparent areas to JPG, the background canvas will be a random color.
def save_image(image, path, hosting_limits, mime_type):
    if path.endswith(settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS['image/jpeg']):
        if image.mode != "RGB":
            # JPEGs can only hold true color images. Formats with other color modes, like .gif, need to be converted first.
            image = image.convert("RGB")
        if mime_type == 'image/jpeg' and 'exif' in image.info:
            # Preserve the EXIF data if the file is a JPEG being saved as a JPEG again. Even if the file is being resized, for now the EXIF dimensions are being left as the original dimensions.
            if 'jpeg_quality' in hosting_limits:
                image.save(path, quality = hosting_limits['jpeg_quality'], exif=image.info['exif'])
            else:
                image.save(path, exif=image.info.get('exif'))
        else:
            if 'jpeg_quality' in hosting_limits:
                image.save(path, quality = hosting_limits['jpeg_quality'])
            else:
                image.save(path)
    else:
        image.save(path)

# 2.4 After file conversion, delete the original if necessary and pick the first in the conversion list as the replacement.
# Update the metadata related to the conversion process.
# Input: Original file, metadata dictionary, the list of extensions used in conversion, the file path without the extension on the end,
# the file path relative to /media/ without the extension on the end (used by Django's database), and the original extension.
# Output: The file picked as the replacement and the metadata dictionary
def post_conversion_update(file, metadata, save_type_list, extless_file_path, extless_file_rel_path, old_ext):
    if old_ext not in save_type_list:
        # First, update the Django model's file path and the metadata to be for the first file in the list.
        metadata['mime_type'] = save_type_list[0]
        metadata['extension'] = settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS[save_type_list[0]]
        file.name = extless_file_rel_path + metadata['extension']
        metadata['file_size'] = file.size
        # Delete the original file because its extension wasn't in the list.
        os.remove(extless_file_path + old_ext)
    if len(save_type_list) > 1:
        # Keep track of all the alternate files' MIME types and sizes. Everything else should be the same.
        metadata['mime_types'] = []
        metadata['sizes'] = []
        for x in range(len(save_type_list)):
            metadata['mime_types'] = metadata['mime_types'] + [save_type_list[x]]
            metadata['sizes'] = metadata['sizes'] + [os.path.getsize(extless_file_path + save_type_list[x])]
    return file, metadata

# 3. Use MoviePy to process the image file. Return the updated file and metadata. The current structure is somewhat flawed in that
# a video may be re-encoded twice, and some tasks could use ffmpeg directly instead of MoviePy.
def process_video(file, metadata, hosting_limits, save_type_list, new_dimensions, gif_dimensions, output_bitrate, needs_bitrate_lowering):
    if 'needs_rotating' in metadata and metadata['needs_rotating']:
        rotate_video(file, output_bitrate)
    else:
        if save_type_list == None and new_dimensions == None and needs_bitrate_lowering:
            # The only task is lowering the bitrate below the cap.
            file, metadata = lower_video_bitrate(file, metadata, hosting_limits, output_bitrate)
    if new_dimensions != None:
        file, metadata = resize_video(file, metadata, hosting_limits, output_bitrate)
    if save_type_list != None:
        file, metadata = convert_video(file, metadata, hosting_limits, output_bitrate, save_type_list, gif_dimensions)
    if 'poster_directory' in hosting_limits:
        create_video_poster(file.path, hosting_limits['poster_directory'])
    if metadata['mime_type'] == 'video/mp4':
        improve_mp4_data(file, metadata, hosting_limits, save_type_list, new_dimensions, needs_bitrate_lowering)
    return file, metadata

# 3.1. Android and iOS devices record width as the longer dimension and height as the shorter dimension, so that they can also record the orientation of the device
# instead of re-encoding. However, for this program, the horizontal dimension must be width and the vertical dimension must be height, or else MoviePy produces a scrambled
# video during other parts of the program -- lowering the bitrate, making the thumbnail, making the poster. This bug may be due to how it uses numpy, rather than a bug in ffmpeg itself,
# because I was able rescale a vertical video with ffmpeg from command line.
def rotate_video(file, output_bitrate):
    name_and_ext = os.path.splitext(file.path)
    original_file_path = file.path
    temporary_file_path = name_and_ext[0] + "_new" + name_and_ext[1]
    command = [FFMPEG_BINARY,
               '-i',
               original_file_path,
               '-c:a',
               'copy',
               '-b:v',
               output_bitrate,
               '-bufsize',
               output_bitrate,
               temporary_file_path]
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        raise IOError(e.output)
    os.remove(file.path)
    os.rename(temporary_file_path, original_file_path)

# 3.2. Save the video file using the original extension and a lower bitrate.
def lower_video_bitrate(file, metadata, hosting_limits, output_bitrate):
    video = VideoFileClip(file.path)
    original_file_path = file.path
    # Temporarily use a different file name, because MoviePy has an error if the input and output path are the same.
    name_and_ext = os.path.splitext(file.path)
    temporary_file_path = name_and_ext[0] + "_new" + name_and_ext[1]
    write_videofile(video, temporary_file_path, output_bitrate, metadata, hosting_limits)

    del video
    process_has_ended = False
    while not process_has_ended:
        try:
            os.rename(file.path,file.path+"_")
            os.rename(file.path+"_",file.path)
            process_has_ended = True
        except PermissionError:
            pass
    # Delete the original file and give the resized file its name.
    os.remove(original_file_path)
    os.rename(temporary_file_path, original_file_path)
    metadata['file_size'] = file.size
    return file, metadata

# 3.2.1. Write to a video file. MoviePy has two separate functions for writing to .gif and video. By examining the extension at the end of the file,
# this function combines them. If you specified the preset option for when the program is writing to MP4, then this program will also pass that
# argument when it detects writing to a .mp4 extension. This function will also, if the hosting limits specified it, convert to .gif with separate
# dimensions.
def write_videofile(video, destination_path, output_bitrate, metadata, hosting_limits, gif_dimensions=None):
    # Even though .gif and .mp4 are almost the only extensions used with these MIME types, this program checks the dictionary for consistency in syntax
    # with cases where the extension can vary and the dictionary is needed to standardize the extension.
    if destination_path.endswith(settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS['image/gif']):
        if gif_dimensions != None:
            video = video.resize(gif_dimensions)
        video.write_gif(destination_path, fps=metadata['fps'])
    else:
        if destination_path.endswith(settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS['video/mp4']):
            write_mp4(video, destination_path, output_bitrate, hosting_limits)
        else:
            video.write_videofile(destination_path, bitrate = output_bitrate)

# 3.2.1.1. Write to an .mp4 file. 
def write_mp4(video, destination_path, output_bitrate, hosting_limits):
    # By default, ffmpeg doesn't do color subsampling, which takes advantage of human visual acuity for colors being lower than
    # human visual acuity for luminosity during encoding. Doing this means ffmpeg has to encode with High 4:4:4 Predictive Profile (Hi444PP, 244).
    # Most software doesn't support decoding this and won't ever support decoding this. The YUV420p color space is used by most major websites
    # including Netflix. Although the default setting or other color spaces make the converted .gif look better, the -pix_fmt yuv420p setting ensures
    # that nearly all video players will be able to see the video. Before I used this setting, videos converted from .gif were invisible in all
    # browsers except Chrome. The -vf scale=trunc(iw/2)*2:trunc(ih/2)*2 setting rounds down the dimensions of the video to an even number. Without
    # this, the -pix_fmt yuv420p setting makes ffmpeg throw an exception.
    if 'preset' in hosting_limits:
        video.write_videofile(destination_path, bitrate = output_bitrate, ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2'], preset = hosting_limits['preset'])
    else:
        video.write_videofile(destination_path, bitrate = output_bitrate, ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2'])

# 3.3. Save the video file using the original extension and lower dimensions.
# Even if more work still needs to be done, ImageIO had an error where it produced a scrambled .gif when converting a resized .MP4 to a .gif without saving between.
# Saving between steps reduces the chance of complex errors within dependencies that only occur during combinations of transformations.
def resize_video(file, metadata, hosting_limits, output_bitrate):
    video = VideoFileClip(file.path)
    video = video.resize(new_dimensions)
    metadata['width'] = new_dimensions[0]
    metadata['height'] = new_dimensions[1]
    original_file_path = file.path
    # Temporarily use a different file name, because MoviePy has an error if the input and output path are the same.
    name_and_ext = os.path.splitext(file.path)
    temporary_file_path = name_and_ext[0] + "_new" + name_and_ext[1]
    write_videofile(video, temporary_file_path, output_bitrate, metadata, hosting_limits)

    del video
    process_has_ended = False
    while not process_has_ended:
        try:
            os.rename(file.path,file.path+"_")
            os.rename(file.path+"_",file.path)
            process_has_ended = True
        except PermissionError:
            pass
    # Delete the original file and give the resized file its name.
    os.remove(original_file_path)
    os.rename(temporary_file_path, original_file_path)
    metadata['file_size'] = file.size
    return file, metadata

# 3.4. Convert the video to all the file types specified by save_type_list. Update the database if a converted file will replace the original.
def convert_video(file, metadata, hosting_limits, output_bitrate, save_type_list, gif_dimensions):
    video = VideoFileClip(file.path)
    extless_file_path, old_ext = os.path.splitext(file.path)
    old_ext = old_ext.lower()
    # Obtain the path relative to \media\ without the extension on the end.
    extless_file_rel_path = os.path.splitext(file.name)[0]
    for x in range(len(save_type_list)):
        # Convert the file using each extension in the list. Skip saving as the original extension.
        if settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS[save_type_list[x]] != old_ext:
            write_videofile(video, extless_file_path + settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS[save_type_list[x]], output_bitrate, metadata, hosting_limits, gif_dimensions)

    # Close the file. There are two factors that make this a complicated action. First, after giving the command to close the file, it may
    # take a few seconds for the MoviePy process to end, but the interpeter is proceeding with subsequent commands. I suspect this is because
    # MoviePy uses ffmpeg, which is multithreaded. If the interpeter gets to a command that needs to access the file, like renaming it or
    # removing it, before the MoviePy process can finish shutting down, on Windows this leads to the exception "PermissionError: [WinError 32]
    # The process cannot access the file because it is being used by another process." This race condition bug occurred very rarely because
    # the process usually finishes shutting down first. Second, closing the file must be done from within the same function body in which the
    # file is opened. When I tried to put closing into a different function, the MoviePy process failed to end until it returned to the parent
    # function. So, this same block of code (without this comment) appears in lower_video_bitrate() and resize_video.
    # On UNIX, the problem manifested as the converted .mp4 not being present on the server, despite the database being updated to know it should
    # look for an .mp4 file. It was found using the same .gif file as the Windows problem.
    del video
    process_has_ended = False
    while not process_has_ended:
        try:
            os.rename(file.path,file.path+"_")
            os.rename(file.path+"_",file.path)
            process_has_ended = True
        except PermissionError:
            pass
    
    file, metadata = post_conversion_update(file, metadata, save_type_list, extless_file_path, extless_file_rel_path, old_ext)
    return file, metadata

# 3.5. Create a .jpg poster for the video, using its first frame.
# Input: file path, directory. The second parameter for the directory allows this function to be used both for the main file and for any thumbnail videos. Output: None
def create_video_poster(file_path, directory):
    video = VideoFileClip(file_path)
    full_file_name = os.path.split(file_path)[1]
    file_name = os.path.splitext(full_file_name)[0]
    destination_path = os.path.join(settings.MEDIA_PATH, TemporaryUpload.UPLOAD_TO, directory, file_name + '.jpg')
    video.save_frame(destination_path)
    
    del video
    process_has_ended = False
    while not process_has_ended:
        try:
            os.rename(file_path,file_path+"_")
            os.rename(file_path+"_",file_path)
            process_has_ended = True
        except PermissionError:
            pass

# 3.6. Handle characteristics that are unique to processing MP4 files.
# First, if the file is ever re-encoded using the libx264 codec, then its dimensions will have to be rounded down to be even or an exception occurs.
# Rather than update the dimensions in the database every time an .mp4 is processed for reasons unrelated to file dimensions, or re-encode the file
# just to make the dimensions are even, so that the database can be 100% accurate, the database width and height are being allowed to differ from reality by a pixel
# or two in these cases.
# Second, the metadata needs to be at the beginning of the file. If it isn't, IE and Firefox won't be able to play the video until it is fully loaded and IE9 won't be able to display it at all.
# 'Atom' refers to a chunk of data within an MP4, and the one named 'moov', the main one for metadata needs to be at the beginning of the file, after the optional ftyp atom. 
# Output: None.
def improve_mp4_data(file, metadata, hosting_limits, save_type_list, new_dimensions, needs_bitrate_lowering):
    metadata['width'] = (metadata['width'] // 2) * 2
    metadata['height'] = (metadata['height'] // 2) * 2
    # The qtfaststart module will check the file and, if necessary, copy it (considerably less expensive than re-encoding) with the moov atom in the
    # right place. I don't use ffmpeg's "-movflags faststart" flag to move the moov atom because on the production server, it made an exception occur
    # when the moov atom was for missing, for unknown reasons. qtfaststart's main function requires a separate input and output path, so the program
    # will write to a different file name and rename the output after deleting the original file.
    qtfaststart(file.path, file.path+"_")
    os.remove(file.path)
    os.rename(file.path+"_",file.path)

# 4. Use the 'thumbnail' key within hosting_limits to save a thumbnail image.
def create_image_thumbnail(file, metadata, hosting_limits):
    new_dimensions = get_thumbnail_dimensions(metadata, hosting_limits)
    destination_path = get_destination_path(file, hosting_limits['thumbnail'][2])
    image = Image.open(file.path)
    image.thumbnail(new_dimensions)
    save_image(image, destination_path, hosting_limits, metadata['mime_type'])

# 4.1 Input: metadata dictionary, hosting_limits dictionary.
# Output: (width, height) tuple of the thumbnail
def get_thumbnail_dimensions(metadata, hosting_limits):
    if hosting_limits['thumbnail'][0] == 'width':
        new_dimensions = (hosting_limits['thumbnail'][1], int( (hosting_limits['thumbnail'][1] / metadata['width']) * metadata['height']) )
    else:
        new_dimensions = (int((hosting_limits['thumbnail'][1] / metadata['height']) * metadata['width']), hosting_limits['thumbnail'][1])
    return new_dimensions

# 4.2. This function generates the path for a corresponding file with the same name, but in a different directory within the directory for processing validated
# files (e.g. media/stage2_processing). Example directory names include "thumbnails" and "posters".
# Input: file, directory string
# Output: String for the path to which the related file will be saved.
def get_destination_path(file, directory):
    # Get the "file.extension" name.
    full_file_name = os.path.split(file.name)[1]
    destination_path = os.path.join(settings.MEDIA_PATH, TemporaryUpload.UPLOAD_TO, directory, full_file_name)
    return destination_path

# 5. Use the 'thumbnail' key within hosting_limits to save a thumbnail video. If there is a 'poster_directory' key, it will also create a thumbnail of the poster
# within a subdirectory of the poster directory. This subdirectory has the same name as the main thumbnail directory.
def create_video_thumbnail(file, metadata, hosting_limits):
    new_dimensions = get_thumbnail_dimensions(metadata, hosting_limits)
    output_bitrate = get_output_bitrate(metadata, hosting_limits, new_dimensions)[0]
    
    destination_path = get_destination_path(file, hosting_limits['thumbnail'][2])
    video = VideoFileClip(file.path)
    video = video.resize(new_dimensions)
    if destination_path.endswith(settings.MIME_TYPES_AND_PREFERRED_EXTENSIONS['video/mp4']):
        write_mp4(video, destination_path, output_bitrate, hosting_limits)
    else:
        video.write_videofile(destination_path, bitrate = output_bitrate)

    del video
    process_has_ended = False
    while not process_has_ended:
        try:
            os.rename(file.path,file.path+"_")
            os.rename(file.path+"_",file.path)
            process_has_ended = True
        except PermissionError:
            pass
        
    if 'poster_directory' in hosting_limits:
        poster_thumbnail_directory = os.path.join(hosting_limits['poster_directory'], hosting_limits['thumbnail'][2])
        create_video_poster(destination_path, poster_thumbnail_directory)
