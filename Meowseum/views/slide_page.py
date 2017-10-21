# Description: This is a page for showing an upload, a file also referred to as a slide, and all the other database information about it.

from Meowseum.models import Upload, Metadata, Comment, Tag, Like, Page, hosting_limits_for_Upload
from Meowseum.forms import CommentForm, TagForm
from django.shortcuts import render, get_object_or_404
from Meowseum.common_view_functions import redirect
from django.utils.http import urlquote_plus
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst
from Meowseum.templatetags.my_filters import humanize_list, format_currency
from django.utils.safestring import mark_safe
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
    
# 0. Main function. Input: request. relative_url refers to a unique code which appears in the URL.
def page(request, relative_url):
    # First, retrieve information about the upload, uploader, and viewer of the page.
    upload = get_object_or_404(Upload, relative_url=relative_url)
    # These variables are related to media paths.
    poster_directory = hosting_limits_for_Upload['poster_directory']
    upload_directory = Upload.UPLOAD_TO
    uploader = upload.uploader.user_profile
    if request.user.is_authenticated():
        viewer = request.user.user_profile
    else:
        viewer = None

    # Next, use these variables to retrieve other information from the database. 
    previous_slide, next_slide = get_surrounding_slide_links(request, upload)
    views = get_unique_views(request, relative_url)
    comments_from_unmuted_users = get_comments_from_unmuted_users(request, upload)
    user_has_liked_this_upload = check_whether_user_has_liked_this_upload(request, upload)
    # Gather information concerning website moderation.
    can_delete_upload, can_ban_users, can_delete_comments = get_permissions(request, upload, uploader, viewer)
    # This is the URL used for the report abuse option in the Follow button dropdown.
    report_abuse_url = reverse('report_abuse') + "?offending_username=" + urlquote_plus(upload.uploader.username) + "&referral_url=" + urlquote_plus(request.path, safe='/')

    context = {'relative_url': relative_url,
               'upload': upload,
               'poster_directory': poster_directory,
               'upload_directory': upload_directory,
               'uploader': uploader,
               'viewer': viewer,
               'previous_slide': previous_slide,
               'next_slide': next_slide,
               'views': views,
               'comments_from_unmuted_users': comments_from_unmuted_users,
               'user_has_liked_this_upload': user_has_liked_this_upload,
               'can_delete_upload': can_delete_upload,
               'can_ban_users': can_ban_users,
               'can_delete_comments': can_delete_comments,
               'report_abuse_url': report_abuse_url,
               # Initialize the page's blank forms.
               'comment_form': CommentForm(),
               'tag_form': TagForm()}
    context = get_pet_information_record(upload, context)
    return render(request, 'en/public/slide_page.html', context)

# 1. Store into 'previous_slide' and 'next_slide' the relative URLs for the neighboring slides in the queryset which the user has most recently been looking at.
# If the user was redirected from the "Random cat" page, this will also make the right arrow link back to the "Random cat" page.
# Input: request, upload.
# Output: previous_slide, next_slide. These variables will contain a string used by the template to determine the URL for slide. 
def get_surrounding_slide_links(request, upload):
    if 'current_gallery' in request.session and len(request.session['current_gallery']) != 0:
        # Store into a variable the previously viewed list of slides from a session storage cookie.
        current_gallery = request.session['current_gallery']
        try:
            # Find the position of the slide within the results list.
            index = current_gallery.index(upload.relative_url)
        except ValueError:
            # The relative URL isn't in the gallery list. The user navigated from another soruce such as a link.
            # Set the index to be the first slide in the gallery page that the user previously viewed.
            index = 0

        # Define the variables using the relative URL for the next or previous index. If the slide is the first in the gallery, hide the previous arrow.
        # If the slide is the last in the gallery, hide the next arrow.
        if index == 0:
            previous_slide = ''
        else:
            previous_slide = current_gallery[index - 1]
        if index == len(current_gallery)-1:
            next_slide = ''
        else:
            next_slide = current_gallery[index + 1]
                
    elif 'random' in request.session:
        # The user naviagated here from the 'Random cat' page.
        # I use this string because I use a system where ? cannot be in a relative URL, so it will never conflict with a user's name for
        # the slide. Then, I decided to write the string like a GET query to make it easier to remember.
        previous_slide = '?previous_slide=random'
        next_slide = '?next_slide=random'
    else:
        # The last gallery viewed had no results, the user didn't navigate here from the gallery and hasn't visited the site before, or the user has disabled cookies.
        # Hide the navigational arrows.
        previous_slide = ''
        next_slide = ''
        
    return previous_slide, next_slide

# 2. Increment the hit count and get an estimate of unique hits, using settings for the django-hitcounts add-on specified in the site's settings.py file.
# Input: request, relative_url.
# Output: views, an integer value.
def get_unique_views(request, relative_url):
    record = Page.objects.get_or_create(name="slide_page", argument1=relative_url)[0]
    hit_count = HitCount.objects.get_for_object(record)
    hit_count_response = HitCountMixin.hit_count(request, hit_count)
    try:
        views = int(hit_count.hits)
    except TypeError:
        # The exception 'TypeError: int() argument must be a string, a bytes-like object or a number, not 'CombinedExpression'" occurred when the page was experiencing its first hit.
        views = 1
    return views

# 3. Retrieve the set of comments for the upload while excluding comments from muted users.
def get_comments_from_unmuted_users(request, upload):
    if request.user.is_authenticated():
        # Because muting is stored on UserProfile and the commenter uses the User object, retrieve an array of User objects.
        muted_users = []
        for profile in request.user.user_profile.muting.all():
            muted_users = muted_users + [profile.user_auth]
        comments_from_unmuted_users = upload.comments.exclude(commenter__in=muted_users)
    else:
        # The user is logged out, so no users are muted.
        comments_from_unmuted_users = upload.comments.all()
    return comments_from_unmuted_users

# 4. Return True if the user has liked this upload. Return False if the user has not liked this upload.
# Input: request, upload.
# Output: user_has_liked_this_upload, True or False.
def check_whether_user_has_liked_this_upload(request, upload):
    user_has_liked_this_upload = False
    if request.user.is_authenticated():
        try:
            like_record = Like.objects.get(upload=upload, liker=request.user)
            user_has_liked_this_upload = True
        except Like.DoesNotExist:
            pass
    return user_has_liked_this_upload

# 5. Return the set of permissions for being able to edit the page, in order to be able to use them as template variables.
# Input: request, upload, uploader, viewer.
# Output: can_delete_upload, can_ban_users, can_delete_comments
def get_permissions(request, upload, uploader, viewer):
    can_delete_upload = False
    if (request.user.has_perm('Meowseum.delete_upload') and not upload.uploader.is_staff) or viewer == uploader:
        # The first part of the predicate is used for deletion through the follow button dropdown menu's moderator-only options. It means that
        # moderators can delete each others' uploads and comments and ban each other, but they can't affect developers with access to the Django admin
        # site. Developer uploads can only be deleted through the admin site except for self-deletion. The second part of the predicate is for the Delete
        # button, through which users delete their own uploads.
        can_delete_upload = True

    can_ban_users = False
    if request.user.has_perm('Meowseum.change_user'):
        can_ban_users = True

    can_delete_comments = False
    if request.user.has_perm('Meowseum.delete_comment'):
        can_delete_comments = True
    return can_delete_upload, can_ban_users, can_delete_comments

# 6. For displaying an Adoption, Lost, or Found record, the output will be more human-readable when the values of form fields on the same topic are merged.
# For example, on the form, it made sense to ask for the overall coat color, coat pattern, and nose color separately, in order to get as much information as possible.
# For the output, the reader doesn't need to see all the labels, so their values are merged beside one "Color:" label.
# As well, there are Boolean fields that shouldn't be shown if the user has entered in the affirmative and then filled out a follow-up question.
# If the user has said the cat has a collar and then described the collar, the user doesn't explicitly need to be told that the cat has a collar.
# The program doesn't test for whether the field has data, because I test for this in the template in order to know whether to include the field's HTML.

# Input: upload, an upload record, and template_variables, the dictionary of variables to be used in the template
# Output: merged_field_labels and merged_field_values are both tuples with corresponding elements for each field.
# boolean_answers is a tuple of strings generated by the Boolean fields for which there isn't follow-up data.
def get_pet_information_record(upload, context):
    upload_category = upload.get_category()

    if upload_category == 'pets':
        return context
    elif upload_category == 'adoption':
        merged_field_labels, merged_field_values, boolean_answers = format_adoption_record_for_display(upload)
    elif upload_category == 'lost':
        merged_field_labels, merged_field_values, boolean_answers = format_lost_record_for_display(upload)
    else:
        if upload.found:
            merged_field_labels, merged_field_values, boolean_answers = format_found_record_for_display(upload)
        
    context['merged_field_labels'] = merged_field_labels
    context['merged_field_values'] = merged_field_values
    context['boolean_answers'] = boolean_answers
    return context

# 6.1 For an Upload record in the Adoption category, merge all the related fields and omit the fields without any relevant information.
# Input: An Upload record. Output: merged_field_labels, merged_field_values, boolean_answers
def format_adoption_record_for_display(upload):
    # Create a tuple for the merged data. Create a separate tuple for the corresponding labels.
    # Unlike a dictionary, this structure will allow a loop to display the fields in the intended order.
    merged_field_labels = ('Name',
                           'Sex',
                           'City',
                           'Breed',
                           'Coat description',
                           'Disabilities',
                           'Prefers a home without',
                           'Age',
                           'Weight',
                           'Energy level',
                           'Bonded with',
                           'ID',
                           'Adoption fee')
    merged_field_values = (upload.adoption.pet_name,
                           get_adoption_merged_sex_field(upload.adoption),
                           get_city_merged_field(upload),
                           get_merged_breed_field(upload.adoption),
                           get_coat_description_field(upload.adoption),
                           capfirst(humanize_list(upload.adoption.disabilities, "")),
                           capfirst(humanize_list(upload.adoption.prefers_a_home_without, "")),
                           get_merged_age_field(upload.adoption),
                           get_merged_weight_field(upload.adoption),
                           capfirst(upload.adoption.energy_level),
                           format_bonded_with_field(upload.adoption.bonded_with.all()),
                           upload.adoption.internal_id,
                           format_currency(upload.adoption.adoption_fee, exact=False))
    boolean_answers = get_adoption_boolean_answers(upload.adoption, merged_field_values[1])
    return merged_field_labels, merged_field_values, boolean_answers

# 6.2. For an Upload record in the Lost category, merge all the related fields and omit the fields without any relevant information.
# Input: An Upload record. Output: merged_field_labels, merged_field_values, boolean_answers
def format_lost_record_for_display(upload):
    microchip_ID, tattoo_ID = get_microchip_or_tattoo_ID(upload.lost)
    
    merged_field_labels = ('Name',
                           'Sex',
                           'City',
                           'Location description',
                           'Collar',
                           'Microchip ID',
                           'Tattoo ID',
                           'Breed',
                           'Coat description',
                           'Eye color',
                           'Nose color',
                           'Other special characteristics',
                           'Disabilities',
                           'Age',
                           'Weight',
                           'Reward')
    merged_field_values = (upload.lost.pet_name,
                           get_lost_merged_sex_field(upload.lost),
                           get_city_merged_field(upload),
                           upload.lost.location,
                           get_collar_merged_field(upload.lost),
                           microchip_ID,
                           tattoo_ID,
                           get_merged_breed_field(upload.lost),
                           get_coat_description_field(upload.lost),
                           get_merged_eye_color_field(upload.lost),
                           capfirst(humanize_list(upload.lost.nose_color)),
                           get_merged_other_special_characteristics_field(upload.lost),
                           capfirst(humanize_list(upload.lost.disabilities, "")),
                           get_merged_age_field(upload.lost),
                           get_merged_weight_field(upload.lost),
                           format_currency(upload.lost.reward, exact=False))
    boolean_answers = get_lost_boolean_answers(upload.lost, merged_field_values[4], merged_field_values[1])
    return merged_field_labels, merged_field_values, boolean_answers

# 6.3. For an Upload record in the Found category, merge all the related fields and omit the fields without any relevant information.
# Input: An Upload record. Output: merged_field_labels, merged_field_values, boolean_answers
def format_found_record_for_display(upload):
    merged_field_labels = ('Name',
                           'Sex',
                           'City',
                           'Location description',
                           'Collar',
                           'Breed',
                           'Coat description',
                           'Eye color',
                           'Nose color',
                           'Other special characteristics',
                           'Disabilities',
                           'Age',
                           'Weight',
                           'ID')
    merged_field_values = (upload.found.pet_name,
                           get_found_merged_sex_field(upload.found),
                           get_city_merged_field(upload),
                           upload.found.location,
                           get_collar_merged_field(upload.found),
                           get_merged_breed_field(upload.found),
                           get_coat_description_field(upload.found),
                           get_merged_eye_color_field(upload.found),
                           capfirst(humanize_list(upload.found.nose_color)),
                           get_merged_other_special_characteristics_field(upload.found),
                           capfirst(humanize_list(upload.found.disabilities, "")),
                           get_merged_age_field(upload.found),
                           get_merged_weight_field(upload.found),
                           upload.found.internal_id)
    boolean_answers = get_found_boolean_answers(upload.found, merged_field_values[4], merged_field_values[1])
    return merged_field_labels, merged_field_values, boolean_answers

# 6.1.1 For the Adoption record, the Sex label will use merged strings for the sex field and the spay/neuter field.
# Input: An Adoption record. Output: The string for the merged field.
def get_adoption_merged_sex_field(record):
    sex = capfirst(record.sex)
    if 'spayed or neutered' in record.has_been:
        if sex == 'Male':
            sex = sex + ', neutered'
        else:
            if sex == 'Female':
                sex = sex + ', spayed'
    return sex

# 6.1.2 The City label will use merged strings for the city, state or province, and ZIP or postal code. These three fields are currently required.
# Input: An Upload record. Output: The string for the merged field.
def get_city_merged_field(upload):
    return upload.uploader.user_contact.city + ", " + upload.uploader.user_contact.state_or_province + " (" + upload.uploader.user_contact.zip_code + ")"

# 6.1.3 The Breed label will use merged strings for the breed field and the hair length field.
# Input: An Adoption, Lost, or Found record. Output: The string for the merged field.
def get_merged_breed_field(record):
    breed = ''
    if record.subtype1 == '':
        # Strictly speaking, not all cats for which the breed option is left blank will be a mix, but most shelters write 'Domestic ___ Hair'
        # for all cats, and the term means the cat is a mix. Even though writing "Mix" at the beginning would be clearer, some cat owners might
        # take exception to their cat being a mix when they didn't explicitly indicate it. So, I left "Mix, " off the beginning.
        if record.hair_length == 'short':
            breed = 'Domestic Short Hair'
        elif record.hair_length == 'medium':
            breed = 'Domestic Medium Hair'
        else:
            if record.hair_length == 'long':
                breed = 'Domestic Long Hair'
    else:
        breed = record.subtype1
        if record.hair_length == 'short':
            breed = breed + " with " + 'short hair'
        elif record.hair_length == 'medium':
            breed = breed + " with " + 'medium hair'
        else:
            if record.hair_length == 'long':
                breed = breed + " with " + 'long hair'
    return breed

# 6.1.4 The Coat description label will use merged strings for the Pattern field, the Color 1 field, the Color 2 field, the fields related to tortoiseshell (multicolor) cats,
# and the 'socks' option under "Other physical characteristics".
# Input: An Adoption, Lost, or Found record. Output: The string for the merged field.
def get_coat_description_field(record):
    coat_description = ''
    if record.pattern == '' and record.color1 != '':
        coat_description = capfirst(record.color1)
        if record.color2 != '':
            # Validate later that the first color field is filled out if the second field is filled out.
            coat_description = coat_description + " and " + record.color2
    elif record.pattern == 'solid':
        # If 'solid' is selected, validate later that the second color field isn't filled out.
        if record.color1 == '':
            coat_description = 'Solid'
        else:
            coat_description = 'Solid' + record.color1
    elif record.pattern == 'tuxedo':
        # If a bicolor pattern is selected, validate later that both color fields are filled out.
        if record.color1 == '':
            coat_description = 'Tuxedo'
        else:
            if record.color1 == 'black' and record.color2 == 'white':
                coat_description = 'Black and white tuxedo cat'
            else:
                coat_description = capfirst(record.color1) + " and " + record.color2 + " in a tuxedo pattern"
    elif record.pattern == 'Van':
        if record.color1 == '' or record.color1 == 'white':
            coat_description = 'Mostly white except for the head and tail'
        else:
            coat_description = capfirst(record.color1) + ' and ' + record.color2 + ', mostly ' + record.color1 + ' except for the head and tail'
    elif record.pattern == 'other bicolor':
        if record.color1 == '':
            coat_description = 'Bicolor'
        else:
            coat_description = capfirst(record.color1)
            if record.color2 != '':
                coat_description = coat_description + " and " + record.color2
    elif record.pattern == 'tabby stripes':
        if record.color1 == '' and record.color2 == '':
            coat_description = 'Tabby'
        else:
            coat_description = capfirst(record.color1)
            if record.color2 != '':
                coat_description = coat_description + ' and ' + record.color2 + 'tabby'
            else:
                coat_description = coat_description + ' tabby'
    elif record.pattern == 'spotted':
        if record.color1 == '' and record.color2 == '':
            coat_description = 'Spotted'
        else:
            # This pattern is relatively rare, so it is the only one that places the pattern first in the coat description.
            if record.color2 == '':
                coat_description = "Spotted " + record.color1
            else:
                coat_description = "Spotted, " + record.color1 + " and " + record.color2
    elif record.pattern == 'tortoiseshell':
        if record.is_calico == None:
            coat_description = 'Tortoiseshell (orange, black, and possibly white)'
        elif record.is_calico == True:
            coat_description = 'Calico (orange, black, and white)'
        elif record.is_calico == False:
            coat_description = 'Orange and black (tortoiseshell) without any white'
        if record.has_tabby_stripes == True:
            coat_description = coat_description + ", with tabby stripes"
        else:
            if record.has_tabby_stripes == False:
                coat_description = coat_description + ", without tabby stripes"
        if record.is_dilute == True:
            coat_description = coat_description + ". " + "The color is dilute, or desaturated like watercolors."
        else:
            if record.is_dilute == False:
                coat_description = coat_description + ". " + "The color is intense or saturated."
    if 'socks' in record.other_physical and record.__class__.__name__ != 'Adoption':
        # If the cat has white paws, and this is a Lost or Found upload, then mention it in the coat description.
        # If this is an Adoption upload, then the socks option is only used while searching.
        # When displaying the record, there isn't a need to be that precise.
        socks_sentence = capfirst(record.possessive_pronoun()) + " paws are white like socks."
        if coat_description == '':
            coat_description = socks_sentence
        else:
            if coat_description.endswith("."):
                coat_description = coat_description + " " + socks_sentence
            else:
                coat_description = coat_description + ". " + socks_sentence
    return coat_description

# 6.1.5 The 'Age' label will merge the field for the age rating (using four qualitiative terms) with the fields for the numerical age in months or years.
# Input: An Adoption, Lost, or Found record. Output: The string for the merged field.
def get_merged_age_field(record):
    age = ''
    if record.age_rating != '':
        age = age + capfirst(record.age_rating)
        if record.precise_age != None:
            age = age + ", " + str(int(record.precise_age)) + " " + record.age_units
            # Later, validate that if the user has filled out the numerical age, that the user has also chosen a unit.
    else:
        if record.precise_age != None:
            age = str(int(record.precise_age)) + " " + record.age_units
    return age

# 6.1.6 The 'Weight' label will merge the fields for the weight and its units.
# Input: An Adoption, Lost, or Found record. Output: The string for the merged field.
def get_merged_weight_field(record):
    weight = ''
    if record.weight != None:
        weight = str(int(record.weight)) + " " + record.weight_units
    return weight

# 6.1.7 Input: A queryset of records for adoptable animals with which this pet has bonded.
# These are the pet's friends and relatives that would be better off taken to one home together when possible.
# Output: HTML for links to each profile.
# If the queryset contains no records, then return an empty string.
def format_bonded_with_field(queryset):
    if queryset == 'Meowseum.Adoption.None':
        return ''
    else:
        list_of_links = []
        for pet in queryset:
            list_of_links = list_of_links + ['<a class="emphasized" href="../' + pet.upload.relative_url + '">'\
                            + pet.pet_name + '</a>']
        return mark_safe(humanize_list(list_of_links))

# 6.1.8 Input: An Adoption record and the merged string with the labels 'Sex'.
# Output: A tuple of strings related to Boolean fields for which the user didn't answer a follow-up question. If there are no entries, the function returns None.
def get_adoption_boolean_answers(record, sex):
    boolean_answers = tuple()
    if sex == '' and 'spayed or neutered' in record.has_been:
        boolean_answers = boolean_answers + ('Spayed or neutered',)
    if 'house trained' in record.has_been:
        boolean_answers = boolean_answers + ('House trained',)
    if 'declawed' in record.has_been:
        boolean_answers = boolean_answers + ('Declawed',)
    if 'vaccinated' in record.has_been:
        boolean_answers = boolean_answers + ('Vaccinations up to date',)
    if 'microchipped' in record.has_been:
        boolean_answers = boolean_answers + ('Microchipped',)
    if 'tested and treated for worms, ticks, and fleas' in record.has_been:
        boolean_answers = boolean_answers + ('Tested and treated for worms, ticks, and fleas',)

    if boolean_answers == tuple():
        # If the tuple is still empty, then store "None" instead so that the condition for showing the field will be clearer.
        boolean_answers = None
    return boolean_answers

# 6.2.1 For the Lost record, the Sex label will use merged strings for the sex field, the spay/neuter field, and the spay/neuter tattoo field.
# Input: A Lost record. Output: The string for the merged field.
def get_lost_merged_sex_field(record):
    sex = capfirst(record.sex)
    if 'spayed or neutered' in record.yes_or_no_questions:
        if sex == 'Male':
            sex = sex + ', neutered'
            if 'has a spay or neuter tattoo' in record.yes_or_no_questions:
                sex = sex + '. Has a neuter tattoo.'
        else:
            if sex == 'Female':
                sex = sex + ', spayed'
                if 'has a spay or neuter tattoo' in record.yes_or_no_questions:
                    sex = sex + '. Has a spay tattoo.'
    return sex

# 6.2.2 The Collar label will use merged strings for the collar color field and the collar description field.
# Input: A Lost or Found record. Output: The string for the merged field.
def get_collar_merged_field(record):
    collar = ''
    if 'has a collar' in record.yes_or_no_questions:
        if record.collar_description != '':
            if record.collar_color != '':
                # If the user has filled out both the "Collar color" and "Collar description" fields, then append the collar color to the description.
                # Use only the "Collar description" field.
                collar = capfirst(record.collar_color) + ". " + record.collar_description
            else:
                collar = record.collar_description
        else:
            if record.collar_color != '':
                # If the user has filled out the "Collar color" field but not the "Collar description" field, then use it instead.
                collar = capfirst(record.collar_color)
    return collar

# 6.2.3 Return the data for the 'Microchip ID' and 'Tattoo ID' labels.
# Input: A Lost record. Output: A string for the microchip ID and a string for the tattoo ID. The site assumes having a microchip and a serial number tattoo are mutually
# exclusive for simplicity, because most sites talk about it in terms of the pros and cons of one or the other. So, at least one of the two outputs will always be an empty string.
def get_microchip_or_tattoo_ID(record):
    microchip_ID = ''
    tattoo_ID = ''
    if record.microchip_or_tattoo_ID != '':
        if 'microchipped' in record.yes_or_no_questions:
            microchip_ID = record.microchip_or_tattoo_ID
        else:
            tattoo_ID = record.microchip_or_tattoo_ID
    return microchip_ID, tattoo_ID

# 6.2.4 The Eye color label will use the merged fields "eye color", "eye color - other", and the heterochromia option under "other physical features".
# Input: A Lost or Found record. Output: The string for the merged field.
def get_merged_eye_color_field(record):
    eye_color = capfirst(record.eye_color)
    # Later, validate against the user checking a radio button that indicates the cat has eyes of one color, while also checking Heterochromia.
    if eye_color == '':
        if record.eye_color_other != '':
            eye_color = capfirst(record.eye_color_other)
            # If the cat has heterochromia and the user has filled out this field, then I'm trusting the user has mentioned it.
        else:
            if 'heterochromia' in record.other_physical:
                eye_color = 'Has a different eye color in each eye.'
    return eye_color

# 6.2.5 The 'Other special characteristics' label will merge the 'Other special characteristics' field with data concerning whether the user checked "Bobtail" or "Polydactyl".
# Input: A Lost or Found record. Output: The string for the merged field.
def get_merged_other_special_characteristics_field(record):
    other_special_characteristics = record.other_special_markings
    if other_special_characteristics != '':
        if 'bobtail' in record.other_physical:
            "Bobtail. " + other_special_characteristics
        if 'polydactyl' in record.other_physical:
            "Polydactyl (more than five toes on at least one paw). " + other_special_characteristics
    return other_special_characteristics

# 6.2.6 Input: A Lost record and the merged strings with the labels 'Sex' and 'Collar'.
# Output: A tuple of strings related to Boolean fields for which the user didn't answer a follow-up question. If there are no entries, the function returns None.
def get_lost_boolean_answers(record, collar, sex):
    boolean_answers = tuple()
    if collar == '' and 'has a collar' in record.yes_or_no_questions:
        boolean_answers = boolean_answers + ('Has a collar',)
    if record.microchip_or_tattoo_ID == '':
        if 'microchipped' in record.yes_or_no_questions:
            boolean_answers = boolean_answers + ('Microchipped',)
        if 'has a tattoo of a serial number' in record.yes_or_no_questions:
            boolean_answers = boolean_answers + ('Has a tattoo of a serial number',)
    if sex == '' and 'spayed or neutered' in record.yes_or_no_questions:
        if 'has a spay or neuter tattoo' in record.yes_or_no_questions:
            boolean_answers = boolean_answers + ('Spayed or neutered, with a spay or neuter tattoo',)
        else:
            boolean_answers = boolean_answers + ('Spayed or neutered',)
    if boolean_answers == tuple():
        # If the tuple is still empty, then store "None" instead so that the condition for showing the field will be clearer.
        boolean_answers = None

    return boolean_answers

# 6.3.1 For the Found record, the Sex label will use merged strings for the sex field and the spay/neuter tattoo field.
# Input: A Found record. Output: The string for the merged field.
def get_found_merged_sex_field(record):
    sex = capfirst(record.sex)
    if 'has a spay or neuter tattoo' in record.yes_or_no_questions:
        if sex == 'Male':
            sex = sex + ', neutered'
        else:
            if sex == 'Female':
                sex = sex + ', spayed'
    return sex

# 6.3.2 Input: A Found record and the merged strings with the labels 'Sex' and 'Collar'.
# Output: A tuple of strings related to Boolean fields for which the user didn't answer a follow-up question. If there are no entries, the function returns None.
def get_found_boolean_answers(record, collar, sex):
    boolean_answers = tuple()
    if collar == '' and 'has a collar' in record.yes_or_no_questions:
        boolean_answers = boolean_answers + ('Has a collar',)
    if sex == '' and 'spayed or neutered' in record.yes_or_no_questions:
        if 'has a spay or neuter tattoo' in record.yes_or_no_questions:
            boolean_answers = boolean_answers + ('Spayed or neutered',)
    if 'no microchip detected during scan' in record.yes_or_no_questions:
        boolean_answers = boolean_answers + ('No microchip detected during scan',)
    if record.is_sighting:
        boolean_answers = booplan_answers + ("This is a sighting report. The uploader doesn't have the cat right now.",)
    if boolean_answers == tuple():
        # If the tuple is still empty, then store "None" instead so that the condition for showing the field will be clearer.
        boolean_answers = None

    return boolean_answers
