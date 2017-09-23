# file_utility_functions_v0_0_4.py by Rachel Bush. Date finished: 
# PROGRAM ID: file_utility_functions.py (_v0_0_4) / File utility functions
# INSTALLATION: Python 3.5, Django 1.9.2
# REMARKS: These are functions related to processing files that are used in more than one location throughout the site.
# VERSION REMARKS: 

import os
import string
import random
from django.core.exceptions import ObjectDoesNotExist
from Meowseum.models import Upload, Metadata

# A. Try to rename or move the file if it exists at the specified location. Do nothing if the file is not there. This is easier than testing for the conditions
# that would lead to a file existing at the source path, such as testing the dimensions of a file for whether it has a thumbnail.
def move_file(source_path, destination_path):
    try:
        os.rename(source_path, destination_path)
    except FileNotFoundError:
        pass

# B. Try to remove the file if it exists at the specified location.
def remove_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

# C.0. This is a higher order function which accepts a string and a Boolean function object. The function object will test whether the string is
# unique for a field in the database. If it is unique, the funcion returns the string, and if it isn't, the function returns the string with an
# underscore and a random seven-character alphanumeric ID. If the string is longer than the maximum amount of characters, then the function truncates
# the part of the string before the underscore and random ID. If the string is an empty string, then the function omits the underscore and only returns
# the random ID.
# Input: string, max_length (int), is_unique function, record. The last argument is optional. It exempts the string from having a random suffix if the
# record argument is the same as the record pulled from the database. The argument being optional allows the function to be used for
# uniqueness-checking before the upload process is complete, and then afterward when renaming the file. For the same reason, the is_unique function
# should have a string argument and an optional record argument.
# Output: string
def make_unique_with_random_id_suffix_within_character_limit(string, max_length, is_unique, record=None):
    string = string[0:max_length]
    if string == '':
        string = id_generator()
        while not is_unique(string, record):
            string = id_generator()
        return string
    else:
        if is_unique(string, record):
            return string
        else:
            if len(string) <= max_length - 8:
                string = string + "_" + id_generator()
            else:
                # Truncate the string if it exceeds the maximum length before appending the random ID.
                string = string[0:max_length-8] + "_" + id_generator()
            while not is_unique(string):
                # Keep generating a random ID until one hasn't been taken.
                string = string[0:len(string)-8] + id_generator()
            return string

# C.1. Return a random string of a certain length, size, from a random set of characters, chars. By default, the string is
# 7 characters long and alphanumeric, because Django uses an underscore and a 7-character alphanumeric ID when a user uploads
# a file with the same name as an existing file.
# Input: size, an integer. chars, a string. Output: A random string.
def id_generator(size=7, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

# D. This Boolean function returns True if the given file name will be unique (case insensitive) and the part of the slide's URL after /slide/ will be unique.
# Input: hypothetical_file_name, a string which excludes the extension. upload record, optional. Output: True or False
def file_name_and_url_will_be_unique(hypothetical_file_name, record=None):
    if file_name_will_be_unique(hypothetical_file_name, record) and url_will_be_unique(hypothetical_file_name, record):
        return True
    else:
        return False

# D.1. This Boolean function returns True if the part of the slide's URL after /slide/ will be unique.
def url_will_be_unique(hypothetical_file_name, record=None):
    try:
        existing_record = Upload.objects.get(relative_url=hypothetical_file_name.replace(" ","_"))
        if record != None and existing_record == record:
            return True
        else:
            return False
    except ObjectDoesNotExist:
        return True

# D.2. This Boolean function queries the database to determine if a file already exists with a given name.
# The query is case insensitive, because many common file systems use case insensitive uniqueness in the same directory.
# The function returns True if the name hasn't been taken yet and False if a file already exists with the name.
def file_name_will_be_unique(hypothetical_file_name, record=None):
    try:
        existing_record = Metadata.objects.get(file_name__iexact=hypothetical_file_name)
        if record != None and existing_record == record.metadata:
            # The user chose a title that is the same as the current file name, which Django already checked for uniqueness.
            return True
        else:
            return False
    except ObjectDoesNotExist:
        return True
