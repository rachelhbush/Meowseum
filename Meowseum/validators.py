# Description: Callable classes and functions in this file validate data for individual fields. Functions are used when the validation has only one
# parameter. This file will also contain functions that take input where the user is allowed to enter it approximately, and return output in a standard
# format (process_noun), but none have been added yet. Validation functions are compatible with testing in the Python shell.

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ObjectDoesNotExist

# This class automatically fulfills one of the four requirements for making a custom validator. The first remaining requirement is taken care of by adding
# a "@deconstructible" decorator above the custom class, which makes Django write the deconstruct() method for you. Second, the class must be in a file directly in the app
# (such as this file). The third remaining requirement is defining __init__(), which is where the subclasses will vary.
class CustomValidator(object):
    # Custom classes must have a __eq__() method comparing attributes with ==, so after the class is serialized, makemigrations can compare model states.
    def __eq__(self, other):
        for attribute in self.__dict__:
            # eval() is safe here because the input, a string for the name of a parmeter in the constructor, is controlled only by the developer.
            if eval("self."+attribute) != eval("other."+attribute):
                return False
        return True

@deconstructible
# Check if a record already exists with this value, for a given model and a given field. Use this class when a model field has unique=True and it
# has a corresponding field in a Form class, or, in a ModelForm, the field will be overriden, in order to avoid a "IntegrityError: UNIQUE
# constraint failed" exception.
class UniquenessValidator(CustomValidator):
    def __init__(self, model, field_name, message):
        self.model = model
        self.field_name = field_name
        self.message = message
    def __call__(self, value):
        try:
            record = self.model.objects.get(**{self.field_name:value})
            raise ValidationError(self.message)
        except ObjectDoesNotExist:
            pass

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
