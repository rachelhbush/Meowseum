# Description: This file is for setting custom sitewide template variables. These variables will be available in every template without first having to define them in a view.
# The top-level functions are referenced by settings.py.

# Define variables that will always be the same throughout the site.
def constant_variables(request):
    # The app_name variable will save a lot of work if the developer decides to rename the app, because it appears in page titles, the footer, etc.
    # It can't be used for image attributes, however, because Django will interpret curly braces within quotation marks literally.
    return {'app_name':'Meowseum'}

# 0. Define variables related to site settings.
def settings_variables(request):
    return {'night_mode':get_night_mode_status(request)}

# 1. Detect whether night mode is on.
# Input: request
# Output: night_mode, a Boolean value for whether night mode is on
def get_night_mode_status(request):
    if 'night_mode' in request.session:
        if request.session['night_mode']:
            return True
        else:
            return False
    else:
        return True
