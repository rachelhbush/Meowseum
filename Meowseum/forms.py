# Description: This file contains all the forms for the site, except for the login and signup forms.
# Each page that includes the site header and its modals will import the blank form and pass the form as a variable to the template.
# The completed form is then sent to a separate view for processing.

from django import forms
from Meowseum.custom_form_fields_and_widgets import HTML5DateInput, HTML5DateField, MultipleChoiceField, CustomModelForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from Meowseum.models import TemporaryUpload, Upload, Tag, Comment, AbuseReport, Feedback, Address, UserContact, Shelter, PetInfo, Adoption, LostFoundInfo, Lost, Found
from Meowseum.file_handling.MetadataRestrictedFileField import MetadataRestrictedFileField
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.core.validators import RegexValidator
from Meowseum.common_view_functions import merge_two_dicts

# Variables used by multiple forms

popular_tags = Tag.get_popular_tag_names() # When no tags have been added to the site yet, the multiselect will appear blank.

# Forms
class SignupForm(CustomModelForm):
    password_confirmation = forms.CharField(max_length=User._meta.get_field('password').max_length, label='', widget=forms.PasswordInput(attrs={"placeholder":"Confirm password"}))
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirmation')
        labels = {'username': '', 'email': '', 'password': ''}
        widgets = {'username': forms.TextInput(attrs={"placeholder":"Username"}),
                   'email': forms.TextInput(attrs={"placeholder":"Email"}),
                   'password': forms.PasswordInput(attrs={"placeholder":"Password"})}
        # Django includes help_text which explains the maximum username length and allowed characters. However, the user doesn't need to see the length because
        # of the maxlength HTML attribute, and the set of allowed characters is close enough to the standard that the user can probably correctly guess the rules.
        # Hide the Django help_text in order to reduce visual clutter and give the user less information to read.
        help_texts = {'username': ''}
        error_messages = {'username': {'unique': 'This username has already been taken.'},
                          'email': {'unique': 'This email address has already been used to create an account.'}}
    def clean(self):
        cleaned_data = super(SignupForm,self).clean()
        # Check whether the first password is identical to the confirmation password.
        password = self.cleaned_data.get('password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if password and password_confirmation and password != password_confirmation:
            raise forms.ValidationError("Passwords are not identical.")
        return self.cleaned_data

class LoginForm(CustomModelForm):
    email_or_username = forms.CharField(label='', widget=forms.TextInput(attrs={"placeholder":"Email or username"}))
    class Meta:
        model = User
        fields = ('email_or_username', 'password')
        labels = {'password':''}
        widgets = {'password': forms.PasswordInput(attrs={"placeholder":"Password"})}
    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        email_or_username = self.cleaned_data.get('email_or_username')
        password = self.cleaned_data.get('password')

        # Check whether the given information corresponds to an existing record in the database.
        if '@' in email_or_username:
            try:
                user = User.objects.get(email=email_or_username)
                username = user.username
                if not authenticate(username=username, password=password):
                    raise forms.ValidationError("Wrong email or password.")
            except User.DoesNotExist:
                raise forms.ValidationError("No account with this email exists.")
        else:
            try:
                user = User.objects.get(username=email_or_username)
                username = email_or_username
                if not authenticate(username=username, password=password):
                    raise forms.ValidationError("Wrong username or password.")
            except User.DoesNotExist:
                raise forms.ValidationError("No account with this username exists.")

        if not user.is_active:
            raise forms.ValidationError("Your account has been disabled.")
        return self.cleaned_data

class FromDeviceForm(CustomModelForm):
    file = MetadataRestrictedFileField()
    def __init__(self, *args, **kwargs):
        super(FromDeviceForm,self).__init__(*args, **kwargs)
        self.fields['file'].required = True
    class Meta:
        model = TemporaryUpload
        fields = ('file',)

class EditUploadForm(CustomModelForm):
    # This is a form for editing the fields of UploadPage1, except for the upload category and tags.
    class Meta:
        model = Upload
        fields = ('title', 'description', 'is_publicly_listed', 'uploader_has_disabled_comments')
        labels = {'title': '', 'description': '',
                  'is_publicly_listed': mark_safe('<span class="bold">Public?</span> Allow the upload to appear in search results. Uploads that are not publicly listed will still be able to be accessed by other users via the URL.')}
        widgets = {'title': forms.TextInput(attrs={"placeholder":"Title (optional)"}),
                   'description': forms.Textarea(attrs={"placeholder":"Description (optional)"})}

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

class UploadPage1(EditUploadForm):
    upload_type = forms.ChoiceField(required=False, choices=(('adoption', 'Up for adoption'), ('lost', 'Lost'), ('found','Found'), ('pets','Pets')), initial='pets', widget=forms.RadioSelect() )
    tags = forms.CharField(required=False, label='Tag list', validators=[validate_tags], initial='#')
    popular_tags = MultipleChoiceField(required=False, label='Browse popular tags', choices=popular_tags)
    class Meta(EditUploadForm.Meta):
        fields = ('title', 'description', 'upload_type', 'tags', 'popular_tags', 'is_publicly_listed', 'uploader_has_disabled_comments')
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        if self.request != None:
            self.CONTACT_INFO_ERROR = mark_safe(render(self.request, 'en/public/missing_contact_information_error_message.html').content.decode('utf-8'))
        super(UploadPage1, self).__init__(*args, **kwargs)
    def clean(self):
        cleaned_data = super(UploadPage1, self).clean()
        upload_type = self.cleaned_data.get('upload_type')
        if upload_type != 'pets' and not self.request.user.user_profile.has_contact_information():
            raise forms.ValidationError(self.CONTACT_INFO_ERROR)
        return self.cleaned_data

class CommentForm(CustomModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': forms.Textarea(attrs={"placeholder":"Write something here..."})}

# This function validates a new tag for an existing upload. # is allowed for the form because it will be stripped during form processing.
def validate_tag(string):
    # Set up the pattern for validating the part of the tag after the #.
    pattern = RegexValidator(r'^[a-zA-z_]+[a-zA-z0-9_]*$', "Make sure the tag contains only letters, digits, and underscores. The first character of a tag cannot be a digit.")
    string = string.lstrip("#")
    # Validate.
    pattern.__call__(string)

class TagForm(CustomModelForm):
    def __init__(self, *args, **kwargs):
        super(TagForm,self).__init__(*args, **kwargs)
        self.fields['name'].validators = [validate_tag]
    class Meta:
        model = Tag
        fields = ('name',)
        widgets = {'name': forms.TextInput(attrs={"value":"#"})}

def validate_offending_username(offending_username):
    try:
        offending_user = User.objects.get(username=offending_username)
    except User.DoesNotExist:
        # If the user doesn't exist, then first check if the user left the field blank.
        # In that case, the error message would be redundant with the "This field is required." message, so it shouldn't be added.
        if offending_username != None:
            raise forms.ValidationError("No user with this username exists.")

class AbuseReportForm(CustomModelForm):
    offending_username = forms.CharField(max_length=User._meta.get_field('username').max_length, label='Offending username', validators=[validate_offending_username])
    def __init__(self, *args, **kwargs):
        super(AbuseReportForm, self).__init__(*args, **kwargs)
    class Meta:
        model = AbuseReport
        fields = ('type_of_abuse', 'offending_username', 'description', 'url')
        widgets = {'url': forms.URLInput}

class FeedbackForm(CustomModelForm):
    screenshot = MetadataRestrictedFileField()
    class Meta:
        model = Feedback
        fields = ('subject', 'comments', 'email', 'screenshot')

class AdvancedSearchForm(forms.Form):
    # This form doesn't include a CustomModelForm because the metadata-related form controls will mostly be different from the Metadata model field. For
    # example, minimum and maximum duration instead of a duration field. I considered including searching for minimum dimensions, but I expect most
    # uploads to be 1080p, so users won't be needing it. Right now, the search engine will only be able to match each word exactly, not account for
    # things like plurals, common misspellings, and common synonyms. Searches will also threaten to overwhelm the server if there are too many. I have
    # heard that if there are more than a few thousand uploads, then I should try using a Django plugin for search indexing, and the most popular one
    # is Haystack.
    filtering_by_photos = forms.BooleanField(required=False)
    filtering_by_gifs = forms.BooleanField(required=False)
    filtering_by_looping_videos_with_audio = forms.BooleanField(required=False)
    min_duration = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"placeholder":"0"}) )
    max_duration = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"placeholder":"60"}) )
    min_fps = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"placeholder":"0"}) )
    all_words = forms.CharField(required=False, max_length = 1000) # AND
    exact_phrase = forms.CharField(required=False, max_length = 1000)
    any_words = forms.CharField(required=False, max_length = 1000) # OR
    exclude_words = forms.CharField(required=False, max_length = 1000) # AND NOT
    # This field enables users to search within another user's posts.
    from_user = forms.CharField(required=False, max_length = User._meta.get_field('username').max_length, widget=forms.TextInput(attrs={"placeholder":"@"}))
    save_search_to_front_page = forms.BooleanField(required=False)

# Forms below this line are used for Meowseum specifically, rather than a general social media site.

class AddressForm(CustomModelForm):
    class Meta:
        model = Address
        fields = ('address_line_1', 'address_line_2', 'city', 'state_or_province', 'country', 'zip_code')

class UserContactForm1(CustomModelForm):
    date_of_birth = HTML5DateField(required=False)
    class Meta:
        model = UserContact
        fields = ('phone_number', 'date_of_birth', 'has_volunteering_interest')
class UserContactForm2(CustomModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class ShelterForm(CustomModelForm):
    class Meta:
        model = Shelter
        fields = ('organization_name', 'contact_first_name', 'contact_last_name', 'contact_title', 'include_contact_in_profile',
                  'profile_phone_number', 'profile_fax_number', 'profile_email', 'website', 'is_nonprofit', 'contact_us_page', 'donation_page',
                  'veterinarian_name', 'veterinarian_phone_number', 'site_contact_first_name', 'site_contact_last_name', 'site_contact_phone_number',
                  'site_contact_email', 'distance_prohibition', 'age_prohibition', 'is_lost_found_meeting_place', 'base_adoption_fee_cat',
                  'base_adoption_fee_kitten', 'services_included_with_adoption_fee')
        labels = {'profile_phone_number': 'Phone number',
                  'profile_fax_number': 'Fax number',
                  'profile_email': 'Email',
                  'veterinarian_name': 'Name',
                  'veterinarian_phone_number': 'Phone number',
                  'site_contact_first_name': 'First name',
                  'site_contact_last_name': 'Last name',
                  'site_contact_phone_number': 'Phone number',
                  'site_contact_email': 'Email'}
        widgets = {'is_nonprofit': forms.RadioSelect,
                   'age_prohibition': forms.NumberInput(attrs={"min":"19"}),
                   'is_lost_found_meeting_place': forms.RadioSelect,
                   'base_adoption_fee_cat': forms.NumberInput(attrs={"placeholder":"0", "class":"currency"}),
                   'base_adoption_fee_kitten': forms.NumberInput(attrs={"placeholder":"0", "class":"currency"})}

class PetInfoForm(CustomModelForm):
    class Meta:
        model = PetInfo
        fields = ('pet_name', 'sex', 'subtype1', 'hair_length', 'pattern', 'is_calico', 'has_tabby_stripes', 'is_dilute', 'color1', 'color2',
                  'age_rating', 'other_physical', 'disabilities', 'weight', 'weight_units', 'precise_age', 'age_units', 'public_contact_information')
        labels = {'public_contact_information': mark_safe('<span class="bold">Public contact information:</span> Check any contact information that you would like to share with the public.')}
        widgets = {'sex': forms.RadioSelect, 'is_dilute': forms.RadioSelect, 'age_rating': forms.RadioSelect}

# Validate the comma-separated list of IDs for pets with which a pet is bonded.
def validate_bonded_with_IDs(string):
    if string != '':
        list_of_IDs = string.split(',')
        # For each internal ID, check whether the ID is valid. The only rule is that an ID can't be an empty string. Then, check whether the cat is in the database.
        for x in range(len(list_of_IDs)):
            list_of_IDs[x] = list_of_IDs[x].lstrip(' ')
            if list_of_IDs[x] == '':
                raise forms.ValidationError("One of the IDs you provided was an empty string.")
            else:
                try:
                    animal = Adoption.objects.get(internal_id=list_of_IDs[x])
                except Adoption.DoesNotExist:
                    raise forms.ValidationError("There is no cat in the database with the following ID: " + list_of_IDs[x])

class AdoptionForm(PetInfoForm):
    # This field uses a comma-separated list in which the user may choose to have spaces following each comma.
    bonded_with_IDs = forms.CharField(required=False, label='Bonded with', validators=[validate_bonded_with_IDs])
    def __init__(self, *args, **kwargs):
        super(AdoptionForm,self).__init__(*args, **kwargs)
        self.fields['pet_name'].required = True
    class Meta(PetInfoForm.Meta):
        model = Adoption
        fields = PetInfoForm.Meta.fields + ('prefers_a_home_without', 'has_been', 'energy_level', 'adoption_fee', 'internal_id', 'bonded_with_IDs', 'euthenasia_soon')
        labels = merge_two_dicts(PetInfoForm.Meta.labels, {'euthenasia_soon': mark_safe('This animal could be euthanized if it is not adopted <em>soon</em>.')})
        widgets = merge_two_dicts(PetInfoForm.Meta.widgets, {'adoption_fee': forms.NumberInput(attrs={"placeholder":"0", "class":"currency"})})
    def clean_internal_id(self):
        # This function is required for an optional unique field.
        return self.cleaned_data['internal_id'] or None
    def clean(self):
        cleaned_data = super(AdoptionForm, self).clean()
        if self.cleaned_data.get('bonded_with_IDs') != '' and self.cleaned_data.get('internal_id') == '':
            raise forms.ValidationError('This "pet ID" field is required in order to fill out the "bonded with" field.')

class LostFoundInfo(PetInfoForm):
    class Meta(PetInfoForm.Meta):
        model = LostFoundInfo
        fields = PetInfoForm.Meta.fields + ('eye_color', 'eye_color_other', 'nose_color', 'location', 'other_special_markings', 'collar_color', 'collar_description')
        labels = merge_two_dicts(PetInfoForm.Meta.labels,
                                 {'other_special_markings': mark_safe('<span class="bold">Other special markings or characteristics?</span> <div>(e.g. tail length, coat pattern)</div>'),
                                  'collar_description': mark_safe('<span class="bold">Collar description</span> (style, materials)')})
        widgets = merge_two_dicts(PetInfoForm.Meta.widgets, {'eye_color': forms.RadioSelect,
                                                             'eye_color_other': forms.TextInput(attrs={"placeholder":"other"})})

class LostForm(LostFoundInfo):
    date = HTML5DateField(label='Date lost')
    def __init__(self, *args, **kwargs):
        super(LostForm,self).__init__(*args, **kwargs)
        self.fields['pet_name'].required = True
    class Meta(LostFoundInfo.Meta):
        model = Lost
        fields = LostFoundInfo.Meta.fields + ('date', 'yes_or_no_questions', 'microchip_or_tattoo_ID', 'reward')
        widgets = merge_two_dicts(LostFoundInfo.Meta.widgets, {'reward': forms.NumberInput(attrs={"placeholder":"0", "class":"currency"})})
 
class FoundForm(LostFoundInfo):
    date = HTML5DateField(label='Date found')
    class Meta(LostFoundInfo.Meta):
        model = Found
        fields = LostFoundInfo.Meta.fields +  ('is_sighting', 'date', 'yes_or_no_questions', 'internal_id')
        widgets = merge_two_dicts(LostFoundInfo.Meta.widgets, {'is_sighting':forms.RadioSelect})
    def clean_internal_id(self):
        # This function is required for an optional unique field.
        return self.cleaned_data['internal_id'] or None

class VerifyDescriptionForm(CustomModelForm):
    # On a lost or found upload form, allow the upload description to be viewed again, this time using an 'Is there anything else?' label.
    class Meta:
        model = Upload
        fields = ('description',)
        labels = {'description': 'Is there any other information that could aid in the return of the pet?'}
