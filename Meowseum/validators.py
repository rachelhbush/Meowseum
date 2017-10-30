# Description: Functions and callable classes and functions in this file validate data for individual fields. Functions are used when the validator will accept
# only one argument, the field data itself, and callable classes are used when the validator will accept other arguments. Validation functions are compatible
# with testing in the Python shell.

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from Meowseum.models import Adoption


# 1. General. This section of the file is for validators which are very general or useful for all models.

# Subclass from this class when creating a validator which accepts multiple arguments. This class automatically fulfills one of the four requirements for making a custom
# validator class. The second requirement is adding a line with the "@deconstructible" decorator above the custom class, which makes Django write the deconstruct() method
# for you. Third, the class must be in a file directly in the app (such as this file). The last requirement is defining __init__(), which is where the subclasses will vary.
class CustomValidator(object):
    # Custom classes must have a __eq__() method comparing attributes with ==, so after the class is serialized, makemigrations can compare model states.
    def __eq__(self, other):
        for attribute in self.__dict__:
            # eval() is safe here because the input, a string for the name of a parmeter in the constructor, is controlled only by the developer.
            if eval("self."+attribute) != eval("other."+attribute):
                return False
        return True

# 2. Model-specific. This section is used to make forms.py shorter.

# This function validates a string of tags for a new upload. Acceptable formats include "blep, catloaf" and "#blep, #catloaf".
def validate_tags(string):
    # If the string is an empty string or contains only characters that will be stripped, then allow the string.
    if string == "" or string=="#" or string==" " or string=="# ":
        return
    # Tags use the same rules as Python variables. If the tag is invalid, the custom error message will be delivered to the template.
    pattern = RegexValidator(r'^[a-zA-z_]+[a-zA-z0-9_]*$', "Make sure all of your tags contain only letters, digits, and underscores. The first character of a tag cannot be a digit.")
    tag_list = string.split(",")
    # Obtain the list without separation by spaces or hashtags.
    for x in range(len(tag_list)):
        tag_list[x] = tag_list[x].lstrip(" ").lstrip("#")
        # Validate the tag. In the console, the error message appears as "django.core.exceptions.ValidationError: ['message']".
        pattern.__call__(tag_list[x])

# This function validates a new tag for an existing upload.
def validate_tag(string):
    # Set up the pattern for validating the part of the tag after the #.
    pattern = RegexValidator(r'^[a-zA-z_]+[a-zA-z0-9_]*$', "Make sure the tag contains only letters, digits, and underscores. The first character of a tag cannot be a digit.")
    string = string.lstrip("#")
    # Validate.
    pattern.__call__(string)

# Validate the comma-separated list of IDs for pets with which a pet is bonded.
def validate_bonded_with_IDs(string):
    if string != '':
        list_of_IDs = string.split(',')
        # For each internal ID, check whether the ID is valid. The only rule is that an ID can't be an empty string. Then, check whether the cat is in the database.
        for x in range(len(list_of_IDs)):
            list_of_IDs[x] = list_of_IDs[x].lstrip(' ')
            if list_of_IDs[x] == '':
                raise ValidationError("One of the IDs you provided was an empty string.")
            else:
                try:
                    animal = Adoption.objects.get(internal_id=list_of_IDs[x])
                except Adoption.DoesNotExist:
                    raise ValidationError("There is no cat in the database with the following ID: " + list_of_IDs[x])

def validate_offending_user(offending_username):
    try:
        offending_user = User.objects.get(username=offending_username)
    except User.DoesNotExist:
        # If the user doesn't exist, then first check if the user left the field blank.
        # In that case, the error message would be redundant with the "This field is required." message, so it shouldn't be added.
        if offending_username != None:
            raise ValidationError("No user with this username exists.")
