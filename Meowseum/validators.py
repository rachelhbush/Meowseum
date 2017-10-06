# Description: Functions and callable classes and functions in this file validate data for individual fields. Functions are used when the validator will accept
# only one argument, the field data itself, and callable classes are used when the validator will accept other arguments. Validation functions are compatible
# with testing in the Python shell.

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import capfirst

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

@deconstructible
# Check if a record already exists with the value the user entered, for a given model and a given field. Use this class when a model field has unique=True and it
# has a corresponding field in a Form class, or, in a ModelForm, the field will be overriden, in order to avoid a "IntegrityError: UNIQUE constraint failed" exception.
# Input (as keyword arguments): model, a class. field_name, a string. error_message, a string (optional). If the last argument is not provided, the function uses
# Django's default "not unique" error message, "[Model name] with this [field's verbose name, with the first letter capitalized] already exists."
# Output: None.
class UniquenessValidator(CustomValidator):
    def __init__(self, model, field_name, error_message='default'):
        self.model = model
        self.field_name = field_name
        if error_message == 'default':
            # Supply Django's default "not unique" error message. The .title() is needed in order for the first letter to be capitalized, but I'm not sure whether Django's
            # default uses titlecase or just capitalizes the first letter. 
            self.error_message = str(model._meta.verbose_name.title()) + " with this " + capfirst(model._meta.get_field(field_name).verbose_name) + " already exists."
        else:
            self.error_message = error_message
    def __call__(self, value):
        try:
            record = self.model.objects.get(**{self.field_name:value})
            raise ValidationError(self.error_message)
        except ObjectDoesNotExist:
            pass

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
