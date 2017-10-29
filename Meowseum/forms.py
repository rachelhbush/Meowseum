# Description: This file contains all the forms for the site, except for the login and signup forms.
# Each page that includes the site header and its modals will import the blank form and pass the form as a variable to the template.
# The completed form is then sent to a separate view for processing.

from django import forms
from Meowseum.custom_form_fields_and_widgets import HTML5DateInput, HTML5DateField, MultipleChoiceField
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from Meowseum.models import TemporaryUpload, Upload, Tag, Comment, AbuseReport, Feedback, UserContact, Shelter, PetInfo, Adoption, LostFoundInfo, Lost, Found, SEX_CHOICES, YES_OR_NO_CHOICES
from Meowseum.file_handling.MetadataRestrictedFileField import MetadataRestrictedFileField
from Meowseum.validators import validate_tags, validate_tag, validate_bonded_with_IDs
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe

# Variables used by multiple forms
popular_tags = Tag.get_popular_tag_names() # When no tags have been added to the site yet, the multiselect will appear blank.

# Forms
class SignupForm(forms.ModelForm):
    password_confirmation = forms.CharField(max_length=128, label='', widget=forms.PasswordInput(attrs={"placeholder":"Confirm password"}))
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

class LoginForm(forms.ModelForm):
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

class FromDeviceForm(forms.ModelForm):
    file = MetadataRestrictedFileField()
    def __init__(self, *args, **kwargs):
        super(FromDeviceForm,self).__init__(*args, **kwargs)
        self.fields['file'].required = True
    class Meta:
        model = TemporaryUpload
        fields = ('file',)

CONTACT_INFO_ERROR = mark_safe("""<div class="form-unit" id="contact-record-warning">To be able to make a listing, first we need your <a href='/user_contact_information' class="emphasized" target="_blank">contact \
information</a>. This information will allow other users to search for listings by geographic location. Shelters and rescue groups will contact you if they have helpful information \
related to your post (found a lost pet, etc). If you are a shelter, <a href='/shelter_contact_information' class="emphasized" target="_blank">register here</a>.</div>""")
class UploadPage1(forms.ModelForm):
    upload_type = forms.ChoiceField(required=False, choices=(('adoption', 'Up for adoption'), ('lost', 'Lost'), ('found','Found'), ('pets','Pets')), initial='pets', widget=forms.RadioSelect() )
    tags = forms.CharField(required=False, label='Tag list', validators=[validate_tags], initial='#')
    popular_tags = MultipleChoiceField(required=False, label='Browse popular tags', choices=popular_tags)
    class Meta:
        model = Upload
        fields = ('title', 'description', 'upload_type', 'tags', 'popular_tags', 'is_publicly_listed', 'uploader_has_disabled_comments')
        labels = {'title': '', 'description': '',
                  'is_publicly_listed': mark_safe('<span class="bold">Public?</span> Allow the upload to appear in search results. Uploads that are not publicly listed will still be able to be accessed by other users via the URL.')}
        widgets = {'title': forms.TextInput(attrs={"placeholder":"Title (optional)"}),
                   'description': forms.Textarea(attrs={"placeholder":"Description (optional)"})}
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UploadPage1, self).__init__(*args, **kwargs)
    def clean(self):
        cleaned_data = super(UploadPage1, self).clean()
        upload_type = self.cleaned_data.get('upload_type')
        if upload_type != 'pets' and not self.request.user.user_profile.has_contact_information():
            raise forms.ValidationError(CONTACT_INFO_ERROR)
        return self.cleaned_data

class EditUploadForm(forms.ModelForm):
    # This is a form for modifying the fields of UploadPage1, except for the upload category and tags.
    title = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder":"Title (optional)"}) )
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"placeholder":"Description (optional)"}) )
    class Meta:
        model = Upload
        fields = ('title', 'description', 'is_publicly_listed', 'uploader_has_disabled_comments')

class CommentForm(forms.ModelForm):
    text = forms.CharField(max_length=10000, widget=forms.Textarea(attrs={"placeholder":"Write something here..."}) )
    class Meta:
        model = Comment
        fields = ('text',)

class TagForm(forms.ModelForm):
    name = forms.CharField(max_length=255, validators=[validate_tag], widget=forms.TextInput(attrs={"value":"#"}) )
    class Meta:
        model = Tag
        fields = ('name',)

class AbuseReportForm(forms.Form):
    offending_username = forms.CharField(max_length=30)
    abuse_type = forms.ChoiceField(choices=(('', 'Select a category'),) + AbuseReport.ABUSE_TYPE_CHOICES, widget=forms.Select())
    abuse_description = forms.CharField(required=False, max_length=100000, widget=forms.Textarea() )
    # This field can be improved by adding validation for whether or not the URL is within the site and whether it returns a 404, if this becomes a problem.
    url = forms.CharField(max_length=255, widget=forms.URLInput() )
    def clean(self):
        # Validate the offending username by checking whether it exists in the database.
        cleaned_data = super(AbuseReportForm, self).clean()
        offending_username = self.cleaned_data.get('offending_username')
        try:
            offending_user = User.objects.get(username=offending_username)
        except User.DoesNotExist:
            # If the user doesn't exist, then first check if the user left the field blank.
            # In that case, the error message would be redundant with the "This field is required." message, so it shouldn't be added.
            if offending_username != None:
                raise forms.ValidationError("No user with this username exists.")
        return self.cleaned_data

class FeedbackForm(forms.ModelForm):
    screenshot = MetadataRestrictedFileField()
    class Meta:
        model = Feedback
        fields = ('subject', 'comments', 'email', 'screenshot')

class AdvancedSearchForm(forms.Form):
    # This form doesn't include a forms.ModelForm because the metadata-related form controls will mostly be different from the Metadata model field. For
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
    from_user = forms.CharField(required=False, max_length = 30, widget=forms.TextInput(attrs={"placeholder":"@"}))
    save_search_to_front_page = forms.BooleanField(required=False)

# Forms below this line are used for Meowseum specifically, rather than a general social media site.

class UserContactForm1(forms.ModelForm):
    date_of_birth = HTML5DateField(required=False)
    class Meta:
        model = UserContact
        fields = ('phone_number', 'address_line_1', 'address_line_2', 'city', 'state_or_province', 'country', 'zip_code', 'date_of_birth', 'has_volunteering_interest')
class UserContactForm2(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ShelterForm(forms.ModelForm):
    is_nonprofit = forms.ChoiceField(choices=YES_OR_NO_CHOICES, widget=forms.RadioSelect())
    age_prohibition = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"min":"19"}) )
    is_lost_found_meeting_place = forms.ChoiceField(required=False, initial=False, choices=YES_OR_NO_CHOICES, widget=forms.RadioSelect())
    base_adoption_fee_cat = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"placeholder":"0", "class":"currency"}) )
    base_adoption_fee_kitten = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"placeholder":"0", "class":"currency"}) )
    class Meta:
        model = Shelter
        fields = ('organization_name', 'contact_first_name', 'contact_last_name', 'contact_title', 'include_contact_in_profile',
                  'profile_address_line_1', 'profile_address_line_2', 'profile_city', 'profile_state_or_province', 'profile_country',
                  'profile_zip_code', 'profile_phone_number', 'profile_fax_number', 'profile_email', 'website', 'is_nonprofit', 'contact_us_page', 'donation_page',
                  'mailing_address_line_1', 'mailing_address_line_2', 'mailing_city', 'mailing_state_or_province', 'mailing_country',
                  'mailing_zip_code', 'veterinarian_name', 'veterinarian_phone_number', 'site_contact_first_name', 'site_contact_last_name',
                  'site_contact_phone_number', 'site_contact_email', 'distance_prohibition', 'age_prohibition', 'is_lost_found_meeting_place',
                  'base_adoption_fee_cat', 'base_adoption_fee_kitten', 'spaying_or_neutering_included', 'vaccination_included', 'microchipping_included',
                  'parasite_treatment_included')

class PetInfoForm(forms.ModelForm):
    sex = forms.ChoiceField(required=False, label='Sex', choices=SEX_CHOICES, widget=forms.RadioSelect())
    is_dilute = forms.NullBooleanField(required=False, label='Dilute?', widget=forms.RadioSelect(choices=PetInfo.IS_DILUTE_CHOICES))
    age_rating = forms.ChoiceField(required=False, label="Rate the cat's age on a scale of 1-4.", choices=PetInfo.AGE_RATING_CHOICES, widget=forms.RadioSelect())
    class Meta:
        model = PetInfo
        fields = ('pet_name', 'sex', 'subtype1', 'hair_length', 'pattern', 'is_calico', 'has_tabby_stripes', 'is_dilute', 'color1', 'color2',
                  'age_rating', 'other_physical', 'disabilities', 'weight', 'weight_units', 'precise_age', 'age_units', 'public_contact_information')
        labels = {'public_contact_information': mark_safe('<span class="bold">Public contact information:</span> Check any contact information that you would like to share with the public.')}

class AdoptionForm(PetInfoForm):
    pet_name = forms.CharField(label='Pet name')
    adoption_fee = forms.FloatField(required=False, label='Adoption fee', widget=forms.NumberInput(attrs={"placeholder":"0", "class":"currency"}) )
    # This field uses a comma-separated list in which the user may choose to have spaces following each comma.
    bonded_with_IDs = forms.CharField(required=False, validators=[validate_bonded_with_IDs])
    class Meta:
        model = Adoption
        fields = PetInfoForm.Meta.fields + ('prefers_a_home_without', 'has_been', 'energy_level', 'adoption_fee', 'internal_id', 'bonded_with_IDs', 'euthenasia_soon')
    def clean_internal_id(self):
        # This function is required for an optional unique field.
        return self.cleaned_data['internal_id'] or None
    def clean(self):
        cleaned_data = super(AdoptionForm, self).clean()
        if self.cleaned_data.get('bonded_with_IDs') != '' and self.cleaned_data.get('internal_id') == '':
            raise forms.ValidationError('This "pet ID" field is required in order to fill out the "bonded with" field.')

class LostFoundInfo(PetInfoForm):
    eye_color = forms.ChoiceField(required=False, choices=LostFoundInfo.CAT_EYE_COLOR_CHOICES, widget=forms.RadioSelect())
    eye_color_other = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder":"other"}) )
    date = HTML5DateField()
    class Meta:
        model = LostFoundInfo
        fields = PetInfoForm.Meta.fields + ('eye_color', 'eye_color_other', 'nose_color', 'date', 'location', 'other_special_markings', 'collar_color', 'collar_description')

class LostForm(LostFoundInfo):
    pet_name = forms.CharField()
    reward = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"placeholder":"0", "class":"currency"}) )
    class Meta:
        model = Lost
        fields = LostFoundInfo.Meta.fields + ('yes_or_no_questions', 'microchip_or_tattoo_ID', 'reward')

class VerifyDescriptionForm(forms.ModelForm):
    # On a lost or found upload form, allow the upload description to be viewed again, this time using an 'Is there anything else?' label.
    class Meta:
        model = Upload
        fields = ('description',)
 
class FoundForm(LostFoundInfo):
    is_sighting = forms.ChoiceField(initial=False, choices=Found.IS_SIGHTING_CHOICES, widget=forms.RadioSelect())
    class Meta:
        model = Found
        fields = LostFoundInfo.Meta.fields +  ('is_sighting', 'yes_or_no_questions', 'internal_id')
    def clean_internal_id(self):
        # This function is required for an optional unique field.
        return self.cleaned_data['internal_id'] or None
