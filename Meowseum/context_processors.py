# Description: This file is for setting custom sitewide template variables. These variables will be available in every template without first having to define them in a view.

def static_variables(request):
    # The app_name variable will save a lot of work if the developer decides to rename the app, because it appears in page titles, the footer, etc.
    # It can't be used for image attributes, however, because Django will interpret curly braces within quotation marks literally.
    return {'app_name':'Meowseum'}
