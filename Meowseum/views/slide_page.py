# Description: This is a page for showing an upload, a file also referred to as a slide, and all the other database information about it.

from Meowseum.models import Upload, Metadata, Comment, Tag, Like, Page, hosting_limits_for_Upload
from Meowseum.forms import CommentForm, TagForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import capfirst
from Meowseum.templatetags.my_filters import humanize_list, format_currency
from django.utils.safestring import mark_safe
from django.template.defaultfilters import urlencode
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from django.utils.timezone import is_aware
from Meowseum.common_view_functions import ajaxWholePageRedirect
    
# 0. Main function. Input: request. relative_url refers to a unique code which appears in the URL.
def page(request, relative_url):
    # First, interpret the URL.
    template_variables = {}
    if " " in relative_url:
        # This allows desktop users to share the slide by pasting the title onto the end of the prefix, while keeping the URL legible in the navigation bar.
        # Most of the time, users will be browsing and sharing using a URL with underscores.
        return HttpResponseRedirect( reverse('slide_page', args=[relative_url.replace(" ","_")]) )
    else:
        try:
            # Retrieve the appropriate slide for the URL.
            upload = Upload.objects.get(relative_url=relative_url)
        except ObjectDoesNotExist:
            # There isn't a slide for this URL, so redirect to the homepage in order to avoid an exception.
            return HttpResponseRedirect(reverse('index'))

    # Next, set up all the remaining variables that will be used by functions in the view.
    template_variables['upload'] = upload
    uploader = upload.uploader.user_profile
    template_variables['uploader'] = uploader
    viewer = None
    if request.user.is_authenticated():
        viewer = request.user.user_profile
        template_variables['viewer'] = viewer
        try:
            like_record = Like.objects.get(upload=upload, liker=request.user)
            template_variables['user_has_liked_this_upload'] = True
        except ObjectDoesNotExist:
            template_variables['user_has_liked_this_upload'] = False
    # Store the absolute URL used for the report abuse option.
    template_variables['report_abuse_url'] = reverse('report_abuse') + "?offending_username=" + urlencode(upload.uploader.username) + "&referral_url=" + urlencode(request.path)
    # Set up permission-related template variables.
    template_variables['can_delete_upload'] = False
    template_variables['can_ban_users'] = False
    template_variables['can_delete_comments'] = False
    if (request.user.has_perm('Meowseum.delete_upload') and not upload.uploader.is_staff) or viewer == uploader:
        # The first part of the predicate is used for deletion through the follow button dropdown menu's moderator-only options. It means that
        # moderators can delete each others' uploads and comments and ban each other, but they can't affect developers with access to the Django admin
        # site. Developer uploads can only be deleted through the admin site except for self-deletion. The second part of the predicate is for the Delete
        # button, through which users delete their own uploads.
        template_variables['can_delete_upload'] = True
    if request.user.has_perm('Meowseum.change_user'):
        template_variables['can_ban_users'] = True
    if request.user.has_perm('Meowseum.delete_comment'):
        template_variables['can_delete_comments'] = True
    # Retrieve other variables used in the template.
    template_variables['poster_directory'] = hosting_limits_for_Upload['poster_directory']
    template_variables['upload_directory'] = Upload.UPLOAD_TO
    # Set up the blank forms for the page that include a field aside from the button itself.
    # If a form is submitted and has errors, it is simpler to replace it later than handle all the invalid conditions.
    template_variables['comment_form'] = CommentForm()
    template_variables['tag_form'] = TagForm()

    # Last, process the data that will be sent to the template or retrieved from the user.
    if request.POST:
        if request.user.is_authenticated():
            return_value = process_data_from_buttons(request, upload, uploader, viewer, template_variables)
            if type(return_value).__name__ == 'HttpResponseRedirect':
                return return_value
            else:
                template_variables = return_value
        else:
            # Redirect to the login page if the logged out user clicks a button that tries to submit a form that would modify the database.
            # Redirect back the user back to the slide page after the user logs in.
            return ajaxWholePageRedirect(request, reverse('login') + "?next="+ urlencode(request.path))

    template_variables = get_surrounding_slide_links(request, upload, template_variables)
    if request.user.is_authenticated():
        template_variables = get_comments_from_unmuted_users(template_variables, upload, viewer)
    else:
        template_variables = get_comments_from_unmuted_users(template_variables, upload)
    template_variables = get_unique_views(request, relative_url, template_variables)

    upload_category = upload.get_category()
    if upload_category != 'pets':
        template_variables = get_pet_information_record(upload, template_variables)
    return render(request, 'en/public/slide_page.html', template_variables)

# 1. This function handles the buttons for liking, following, muting, commenting, and tagging.
# If the page is being reloaded because of one of these actions, then process and save the data.
def process_data_from_buttons(request, upload, uploader, viewer, template_variables):
    # Identify which form was submitted by retrieving a value from the submit button.
    submission_type = request.POST.get('submission_type')

    # First, redirect to separate separate views. This happens for users with JavaScript disabled, as well as the rare user who performs an action via the URL bar.
    # The redirects use a querystring to record the URL. Hidden form controls won't work because the submitted form is being sent back to this view, or else there wouldn't
    # be a neeed for the redirects.
    if submission_type == 'like':
        return HttpResponseRedirect( reverse('like', args=[relative_url]))
    elif submission_type == 'follow':
        return HttpResponseRedirect( reverse('follow', args=[upload.uploader.username]) + "?next="+ urlencode(request.path))
    elif submission_type == 'comment':
        # Set up the form where the user can comment on the slide.
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            # Save the comment form.
            new_comment_record = comment_form.save(commit=False)
            new_comment_record.commenter = request.user
            new_comment_record.upload = upload
            new_comment_record.save()
        else:
            template_variables['comment_form'] = comment_form
    elif submission_type == 'tag':
        # Set up the form where any user can add a new tag to the slide.
        tag_form = TagForm(request.POST)
        if tag_form.is_valid():
            name = tag_form.cleaned_data['name'].lstrip("#").lower()
            try:
                # If the tag does exist, then associate this upload record with it.
                existing_tag = Tag.objects.get(name=name)
                existing_tag.uploads.add(upload)
                existing_tag.save()
            except ObjectDoesNotExist:
                # If the tag doesn't exist, create a new one and add the most recent upload as the first record.
                new_tag = Tag(name=name)
                new_tag.save()
                new_tag.uploads.add(upload)
                new_tag.save()
        else:
            template_variables['tag_form'] = tag_form
    else:
        if 'delete_comment' in submission_type and template_variables['can_delete_comments']:
            comment_id = int(submission_type.lstrip('delete_comment_'))
            comment = Comment.objects.get(id=comment_id)
            if not comment.commenter.is_staff:
                comment.delete()
    return template_variables

# 2. Store into 'previous_slide' and 'next_slide' the relative URLs for the neighboring slides in the queryset which the user has most recently been looking at.
# If the user was redirected from the "Random cat" page, this will also make the right arrow link back to the "Random cat" page.
def get_surrounding_slide_links(request, upload, template_variables):
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
            template_variables['previous_slide'] = ''
        else:
            template_variables['previous_slide'] = current_gallery[index - 1]
        if index == len(current_gallery)-1:
            template_variables['next_slide'] = ''
        else:
            template_variables['next_slide'] = current_gallery[index + 1]
                
    elif 'random' in request.session:
        # The user naviagated here from the 'Random cat' page.
        # I use this string because I use a system where ? cannot be in a relative URL, so it will never conflict with a user's name for
        # the slide. Then, I decided to write the string like a GET query to make it easier to remember.
        template_variables['previous_slide'] = '?previous_slide=random'
        template_variables['next_slide'] = '?next_slide=random'
    else:
        # The last gallery viewed had no results, the user didn't navigate here from the gallery and hasn't visited the site before, or the user has disabled cookies.
        # Hide the navigational arrows.
        template_variables['previous_slide'] = ''
        template_variables['next_slide'] = ''
        
    return template_variables

# 3. Retrieve the set of comments for the upload while excluding comments from muted users.
def get_comments_from_unmuted_users(template_variables, upload, viewer=None):
    if viewer == None:
        # The user is logged out, so no users are muted.
        template_variables['comments_from_unmuted_users'] = upload.comments.all()
    else:
        # Because muting is stored on UserProfile and the commenter uses the User object, retrieve an array of User objects.
        muted_users = []
        for profile in viewer.muting.all():
            muted_users = muted_users + [profile.user_auth]
        comments_from_unmuted_users = upload.comments.exclude(commenter__in=muted_users)
        template_variables['comments_from_unmuted_users'] = comments_from_unmuted_users
    return template_variables

# 4. Increment the hit count and get an estimate of unique hits, using settings for the django-hitcounts add-on specified in the site's settings.py file.
# Input: request, the relative_url argument, template_variables
# Output: The function adds the 'views' key with an integer value to template_variables.
def get_unique_views(request, relative_url, template_variables):
    record = Page.objects.get_or_create(name="slide_page", argument1=relative_url)[0]
    hit_count = HitCount.objects.get_for_object(record)
    hit_count_response = HitCountMixin.hit_count(request, hit_count)
    try:
        template_variables['views'] = int(hit_count.hits)
    except TypeError:
        # The exception 'TypeError: int() argument must be a string, a bytes-like object or a number, not 'CombinedExpression'" occurred when the page was experiencing its first hit.
        template_variables['views'] = 1
    return template_variables

# 5. For displaying an Adoption, Lost, or Found record, the output will be more human-readable when the values of form fields on the same topic are merged.
# For example, on the form, it made sense to ask for the overall coat color, coat pattern, and nose color separately, in order to get as much information as possible.
# For the output, the reader doesn't need to see all the labels, so their values are merged beside one "Color:" label.
# As well, there are Boolean fields that shouldn't be shown if the user has entered in the affirmative and then filled out a follow-up question.
# If the user has said the cat has a collar and then described the collar, the user doesn't explicitly need to be told that the cat has a collar.
# The program doesn't test for whether the field has data, because I test for this in the template in order to know whether to include the field's HTML.

# Input: upload, an upload record, and template_variables, the dictionary of variables to be used in the template
# Output: merged_field_labels and merged_field_values are both tuples with corresponding elements for each field.
# boolean_answers is a tuple of strings generated by the Boolean fields for which there isn't follow-up data.
def get_pet_information_record(upload, template_variables):
    if upload.adoption:
        merged_field_labels, merged_field_values, boolean_answers = format_adoption_record_for_display(upload)
    elif upload.lost:
        merged_field_labels, merged_field_values, boolean_answers = format_lost_record_for_display(upload)
    else:
        if upload.found:
            merged_field_labels, merged_field_values, boolean_answers = format_found_record_for_display(upload)
        
    template_variables['merged_field_labels'] = merged_field_labels
    template_variables['merged_field_values'] = merged_field_values
    template_variables['boolean_answers'] = boolean_answers
    return template_variables

# 5.1 For an Upload record in the Adoption category, merge all the related fields and omit the fields without any relevant information.
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
                           'Age',
                           'Weight',
                           'Energy level',
                           'Bonded with',
                           'Adoption fee')
    merged_field_values = (upload.adoption.pet_name,
                           get_adoption_merged_sex_field(upload.adoption),
                           get_city_merged_field(upload),
                           get_merged_breed_field(upload.adoption),
                           get_coat_description_field(upload.adoption),
                           capfirst(humanize_list(upload.adoption.disabilities, "")),
                           get_merged_age_field(upload.adoption),
                           get_merged_weight_field(upload.adoption),
                           capfirst(upload.adoption.energy_level),
                           format_bonded_with_field(upload.adoption.bonded_with.all()),
                           format_currency(upload.adoption.adoption_fee, exact=False))
    boolean_answers = get_adoption_boolean_answers(upload.adoption, merged_field_values[1])
    return merged_field_labels, merged_field_values, boolean_answers

# 5.2. For an Upload record in the Lost category, merge all the related fields and omit the fields without any relevant information.
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

# 5.3. For an Upload record in the Found category, merge all the related fields and omit the fields without any relevant information.
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
                           'Weight')
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
                           get_merged_weight_field(upload.found))
    boolean_answers = get_found_boolean_answers(upload.found, merged_field_values[4], merged_field_values[1])
    return merged_field_labels, merged_field_values, boolean_answers

# 5.1.1 For the Adoption record, the Sex label will use merged strings for the sex field and the spay/neuter field.
# Input: An Adoption record. Output: The string for the merged field.
def get_adoption_merged_sex_field(record):
    sex = capfirst(record.sex)
    if record.spayed_or_neutered:
        if sex == 'Male':
            sex = sex + ', neutered'
        else:
            if sex == 'Female':
                sex = sex + ', spayed'
    return sex

# 5.1.2 The City label will use merged strings for the city, state or province, and ZIP or postal code. These three fields are currently required.
# Input: An Upload record. Output: The string for the merged field.
def get_city_merged_field(upload):
    return upload.uploader.user_contact.city + ", " + upload.uploader.user_contact.state_or_province + " (" + upload.uploader.user_contact.zip_code + ")"

# 5.1.3 The Breed label will use merged strings for the breed field and the hair length field.
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

# 5.1.4 The Coat description label will use merged strings for the Pattern field, the Color 1 field, the Color 2 field, the fields related to tortoiseshell (multicolor) cats,
# and the 'socks' option under "Other physical characteristics".
# Input: An Adoption, Lost, or Found record. Output: The string for the merged field.
def get_coat_description_field(record):
    coat_description = ''
    if record.pattern == 'solid':
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
    elif record.pattern == 'Tabby stripes':
        if record.color1 == '' and record.color2 == '':
            coat_description = 'Tabby'
        else:
            coat_description = capfirst(record.color1)
            if record.color2 != '':
                coat_description = coat_description + ' and ' + record.color2 + 'tabby'
            else:
                coat_description = coat_description + ' tabby'
    elif record.pattern == 'Spotted':
        if record.color1 == '' and record.color2 == '':
            coat_description = 'Spotted'
        else:
            # This pattern is relatively rare, so it is the only one that places the pattern first in the coat description.
            if record.color2 == '':
                coat_description = "Spotted " + record.color1
            else:
                coat_description = "Spotted, " + record.color1 + " and " + record.color2
    elif record.pattern == 'Tortoiseshell':
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
        socks_sentence = capfirst(record.posessive_pronoun()) + " paws are white like socks."
        if coat_description.endswith("."):
            coat_description = coat_description + " " + socks_sentence
        else:
            coat_description = coat_description + ". " + socks_sentence
    return coat_description

# 5.1.5 The 'Age' label will merge the field for the age rating (using four qualitiative terms) with the fields for the numerical age in months or years.
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

# 5.1.6 The 'Weight' label will merge the fields for the weight and its units.
# Input: An Adoption, Lost, or Found record. Output: The string for the merged field.
def get_merged_weight_field(record):
    weight = ''
    if record.weight != None:
        weight = str(int(record.weight)) + " " + record.weight_units
    return weight

# 5.1.7 Input: A queryset of records for adoptable animals with which this pet has bonded.
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

# 5.1.8 Input: An Adoption record and the merged string with the labels 'Sex'.
# Output: A tuple of strings related to Boolean fields for which the user didn't answer a follow-up question. If there are no entries, the function returns None.
def get_adoption_boolean_answers(record, sex):
    boolean_answers = tuple()
    if sex == '' and record.spayed_or_neutered:
        boolean_answers = boolean_answers + ('Spayed or neutered',)
    if record.house_trained:
        boolean_answers = boolean_answers + ('House trained',)
    if record.declawed:
        boolean_answers = boolean_answers + ('Declawed',)
    if record.vaccinated:
        boolean_answers = boolean_answers + ('Vaccinations up to date',)
    if record.microchipped:
        boolean_answers = boolean_answers + ('Microchipped',)
    if record.parasite_free:
        boolean_answers = boolean_answers + ('Tested and treated for worms, ticks, and fleas',)
    likes = get_likes_string(record)
    if likes != None:
        boolean_answers = boolean_answers + (likes,)

    if boolean_answers == tuple():
        # If the tuple is still empty, then store "None" instead so that the condition for showing the field will be clearer.
        boolean_answers = None
    return boolean_answers

# 5.1.7.1 Merge the Boolean "Gets along well with" fields so that the "Gets along well with" part won't be repeated several times.
# Input: An Adoption record. Output: The string for the merged fields. If the cat is not on record as getting along well with anything, then return None.
def get_likes_string(record):
    if record.likes_cats or record.likes_dogs or record.likes_kids:
        likes_list = []
        if record.likes_cats:
            likes_list = likes_list + ['other cats']
        if record.likes_dogs:
            likes_list = likes_list + ['dogs']
        if record.likes_kids:
            if record.likes_kids_age == None:
                likes_list = likes_list + ['children']
            else:
                likes_list = likes_list + ['children down to age ' + str(record.likes_kids_age)]
        return 'Gets along well with ' + humanize_list(likes_list)
    else:
        return None

# 5.2.1 For the Lost record, the Sex label will use merged strings for the sex field, the spay/neuter field, and the spay/neuter tattoo field.
# Input: A Lost record. Output: The string for the merged field.
def get_lost_merged_sex_field(record):
    sex = capfirst(record.sex)
    if record.spayed_or_neutered:
        if sex == 'Male':
            sex = sex + ', neutered'
            if record.has_spay_or_neuter_tattoo:
                sex = sex + '. Has a neuter tattoo.'
        else:
            if sex == 'Female':
                sex = sex + ', spayed'
                if record.has_spay_or_neuter_tattoo:
                    sex = sex + '. Has a spay tattoo.'
    return sex

# 5.2.2 The Collar label will use merged strings for the collar color field and the collar description field.
# Input: A Lost or Found record. Output: The string for the merged field.
def get_collar_merged_field(record):
    collar = ''
    if record.has_collar:
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

# 5.2.3 Return the data for the 'Microchip ID' and 'Tattoo ID' labels.
# Input: A Lost record. Output: A string for the microchip ID and a string for the tattoo ID. The site assumes having a microchip and a serial number tattoo are mutually
# exclusive for simplicity, because most sites talk about it in terms of the pros and cons of one or the other. So, at least one of the two outputs will always be an empty string.
def get_microchip_or_tattoo_ID(record):
    microchip_ID = ''
    tattoo_ID = ''
    if record.id_number_description != '':
        if record.microchipped:
            microchip_ID = record.id_number_description
        else:
            tattoo_ID = record.id_number_description
    return microchip_ID, tattoo_ID

# 5.2.4 The Eye color label will use the merged fields "eye color", "eye color - other", and the heterochromia option under "other physical features".
# Input: A Lost or Found record. Output: The string for the merged field.
def get_merged_eye_color_field(record):
    eye_color = record.eye_color
    # Later, validate against the user checking a radio button that indicates the cat has eyes of one color, while also checking Heterochromia.
    if eye_color == '':
        if record.eye_color_other != '':
            eye_color = capfirst(record.eye_color_other)
            # If the cat has heterochromia and the user has filled out this field, then I'm trusting the user has mentioned it.
        else:
            if 'Heterochromia' in record.other_physical:
                eye_color = 'Has a different eye color in each eye.'
    return eye_color

# 5.2.5 The 'Other special characteristics' label will merge the 'Other special characteristics' field with data concerning whether the user checked "Bobtail" or "Polydactyl".
# Input: A Lost or Found record. Output: The string for the merged field.
def get_merged_other_special_characteristics_field(record):
    other_special_characteristics = record.other_special_markings
    if other_special_characteristics != '':
        if 'bobtail' in record.other_physical:
            "Bobtail. " + other_special_characteristics
        if 'polydactyl' in record.other_physical:
            "Polydactyl (more than five toes on at least one paw). " + other_special_characteristics
    return other_special_characteristics

# 5.2.6 Input: A Lost record and the merged strings with the labels 'Sex' and 'Collar'.
# Output: A tuple of strings related to Boolean fields for which the user didn't answer a follow-up question. If there are no entries, the function returns None.
def get_lost_boolean_answers(record, collar, sex):
    boolean_answers = tuple()
    if collar == '' and record.has_collar:
        boolean_answers = boolean_answers + ('Has a collar',)
    if record.id_number_description == '':
        if record.microchipped:
            boolean_answers = boolean_answers + ('Microchipped',)
        else:
            if record.has_serial_number_tattoo:
                boolean_answers = boolean_answers + ('Has a serial number tattoo',)
    if sex == '' and record.spayed_or_neutered:
        if record.has_spay_or_neuter_tattoo:
            boolean_answers = boolean_answers + ('Spayed or neutered, with a spay or neuter tattoo',)
        else:
            boolean_answers = boolean_answers + ('Spayed or neutered',)
    if boolean_answers == tuple():
        # If the tuple is still empty, then store "None" instead so that the condition for showing the field will be clearer.
        boolean_answers = None

    return boolean_answers

# 5.3.1 For the Found record, the Sex label will use merged strings for the sex field and the spay/neuter tattoo field.
# Input: A Found record. Output: The string for the merged field.
def get_found_merged_sex_field(record):
    sex = capfirst(record.sex)
    if record.has_spay_or_neuter_tattoo:
        if sex == 'Male':
            sex = sex + ', neutered'
        else:
            if sex == 'Female':
                sex = sex + ', spayed'
    return sex

# 5.3.2 Input: A Found record and the merged strings with the labels 'Sex' and 'Collar'.
# Output: A tuple of strings related to Boolean fields for which the user didn't answer a follow-up question. If there are no entries, the function returns None.
def get_found_boolean_answers(record, collar, sex):
    boolean_answers = tuple()
    if collar == '' and record.has_collar:
        boolean_answers = boolean_answers + ('Has a collar',)
    if sex == '' and record.spayed_or_neutered:
        if record.has_spay_or_neuter_tattoo:
            boolean_answers = boolean_answers + ('Spayed or neutered',)
    if record.no_microchip:
        boolean_answers = boolean_answers + ('No microchip detected during scan',)
    if record.is_sighting:
        boolean_answers = booplan_answers + ("This is a sighting report. The uploader doesn't have the cat right now.",)
    if boolean_answers == tuple():
        # If the tuple is still empty, then store "None" instead so that the condition for showing the field will be clearer.
        boolean_answers = None

    return boolean_answers
