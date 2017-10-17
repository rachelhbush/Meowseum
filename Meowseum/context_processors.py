# Description: This file is for setting custom sitewide template variables. These variables will be available in every template without first having to define them in a view.
# The top-level functions are referenced by settings.py.

# Define variables that will always be the same throughout the site.
def constant_variables(request):
    # The app_name variable will save a lot of work if the developer decides to rename the app, because it appears in page titles, the footer, etc.
    # It can't be used for image attributes, however, because Django will interpret curly braces within quotation marks literally. The domain name
    # will probably change during production depending on which domain name ideas are available and affordable.
    return {'app_name':'Meowseum', 'domain_name': 'meowseum.tk'}

# 0. Define variables related to site settings.
def settings_variables(request):
    return {'night_mode':get_night_mode_status(request),  'mobile_GIFs_are_playing': get_mobile_play_button_status(request)}

# 1. Detect whether night mode is on.
# Input: request. Output: night_mode, a Boolean value for whether night mode is on.
def get_night_mode_status(request):
    if 'night_mode' in request.session and not request.session['night_mode']:
        return False
    else:
        return True

# 2. Detect whether the mobile play button has been pressed.
# Input: request. Output: mobile_GIFs_are_playing, a Boolean value for whether GIFs in galleries are currently playing on mobile devices.
def get_mobile_play_button_status(request):
    if 'mobile_GIFs_are_playing' in request.session and not request.session['mobile_GIFs_are_playing']:
        return False
    else:
        return True
