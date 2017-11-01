# Description: This file is for validators which are general or useful for all models. The validators which are specific to a model are in models.py, and the
# validators which are specific to forms are in forms.py,  in order to avoid circular imports. Validators can be functions or callable classes. Functions are
# used when the validator will accept only one argument, the field data itself, and callable classes are used when the validator will accept other arguments.
# Validation functions are compatible with testing in the Python shell.

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

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
