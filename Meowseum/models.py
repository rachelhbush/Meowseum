# Description: This file contains the project's models -- databases structured using object-oriented programming.
# Class attributes correspond to the header row of a spreadsheet, and object attributes correspond to the record rows.
# When I want to store all of a model's information related to a certain topic, I store everything related to the topic in another model and use a one-to-one-relationship.
# Every Upload has a Metadata record. This organization is like nesting a JSON object or dictionary in another.
# Summary of models for Ctrl+F navigation: Page, ExceptionRecord, TemporaryUpload, Upload, Metadata, Tag, Like, Comment, UserProfile, AbuseReport, Feedback, UserContact, Shelter,
#                                          Adoption, Lost, Found

from django.db import models
from Meowseum.custom_form_fields_and_widgets import MultipleChoiceField
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django import forms
from hitcount.models import HitCountMixin
from Meowseum.file_handling.MetadataRestrictedFileField import MetadataRestrictedFileField
from Meowseum.file_handling.CustomStorage import CustomStorage
from django.db.models import Count
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from django.utils.safestring import mark_safe

YES_OR_NO_CHOICES = ((True, 'Yes'), (False, 'No'))
SEX_CHOICES = (('male', 'Male'), ('female', 'Female'))
# The regions supported are currently the U.S. and Canada.
COUNTRY_CHOICES = (('United States', 'United States'), ('Canada', 'Canada'))
STATE_OR_PROVINCE_CHOICES = (('Alberta', 'Alberta'),
                             ('Alabama', 'Alabama'),
                             ('Alaska', 'Alaska'),
                             ('Arizona', 'Arizona'),
                             ('Arkansas', 'Arkansas'),
                             ('British Columbia', 'British Columbia'),
                             ('California', 'California'),
                             ('Colorado', 'Colorado'),
                             ('Connecticut', 'Connecticut'),
                             ('Delaware', 'Delaware'),
                             ('District of Columbia', 'District of Columbia'),
                             ('Florida', 'Florida'),
                             ('Georgia', 'Georgia'),
                             ('Guam', 'Guam'),
                             ('Hawaii', 'Hawaii'),
                             ('Idaho', 'Idaho'),
                             ('Illinois', 'Illinois'),
                             ('Indiana', 'Indiana'),
                             ('Iowa', 'Iowa'),
                             ('Kansas', 'Kansas'),
                             ('Kentucky', 'Kentucky'),
                             ('Louisiana', 'Louisiana'),
                             ('Maine', 'Maine'),
                             ('Manitoba', 'Manitoba'),
                             ('Maryland', 'Maryland'),
                             ('Massachusetts', 'Massachusetts'),
                             ('Michigan', 'Michigan'),
                             ('Minnesota', 'Minnesota'),
                             ('Mississippi', 'Mississippi'),
                             ('Missouri', 'Missouri'),
                             ('Montana', 'Montana'),
                             ('Nebraska', 'Nebraska'),
                             ('Nevada', 'Nevada'),
                             ('New Brunswick', 'New Brunswick'),
                             ('New Hampshire', 'New Hampshire'),
                             ('New Jersey', 'New Jersey'),
                             ('New Mexico', 'New Mexico'),
                             ('New York', 'New York'),
                             ('Newfoundland and Labrador', 'Newfoundland and Labrador'),
                             ('North Carolina', 'North Carolina'),
                             ('North Dakota', 'North Dakota'),
                             ('Northwest Territories', 'Northwest Territories'),
                             ('Nova Scotia', 'Nova Scotia'),
                             ('Nuvanut', 'Nuvanut'),
                             ('Ohio', 'Ohio'),
                             ('Oklahoma', 'Oklahoma'),
                             ('Ontario', 'Ontario'),
                             ('Oregon', 'Oregon'),
                             ('Puerto Rico', 'Puerto Rico'),
                             ('Pennsylvania', 'Pennsylvania'),
                             ('Prince Edward Island', 'Prince Edward Island'),
                             ('Quebec', 'Quebec'),
                             ('Rhode Island', 'Rhode Island'),
                             ('Saskatchewan', 'Saskatchewan'),
                             ('South Carolina', 'South Carolina'),
                             ('South Dakota', 'South Dakota'),
                             ('Tennessee', 'Tennessee'),
                             ('Texas', 'Texas'),
                             ('Utah', 'Utah'),
                             ('Virgin Islands', 'Virgin Islands'),
                             ('Vermont', 'Vermont'),
                             ('Virginia', 'Virginia'),
                             ('Washington', 'Washington'),
                             ('West Virginia', 'West Virginia'),
                             ('Wisconsin', 'Wisconsin'),
                             ('Wyoming', 'Wyoming'),
                             ('Yukon Territory', 'Yukon Territory'))

# Custom model fields.
class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices. Uses Django 1.11's postgres ArrayField
    and a MultipleChoiceField for its formfield, with a checkbox group as the default widget.
    """
 
    def formfield(self, **kwargs):
        defaults = {
            'form_class': MultipleChoiceField,
            'choices': self.base_field.choices,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't care for it.
        # pylint:disable=bad-super-call
        return super(ArrayField, self).formfield(**defaults)

class Page(models.Model):
    # This model is used with django-hitcount to keep track of page views across the site. The first field is the DRY name of the page in urls.py.
    name = models.CharField(max_length=255, verbose_name="name")
    # The second field is the first optional argument used with the URL.
    # The model doesn't keep track of querystrings because it would be easier to keep track of search statistics with a separate model.
    argument1 = models.CharField(max_length=255, verbose_name="argument1", default="", blank=True)
    def __str__(self):
        if self.argument1 == '':
            return self.name
        else:
            return self.name + ": " + self.argument1

class ExceptionRecord(models.Model):
    # This model is used with ExceptionLoggingMiddleware.
    path = models.TextField(max_length=10000, verbose_name="path")
    # The next two fields can be used for querying and statistics on how often certain exceptions occur.
    exception_type = models.CharField(max_length=100, verbose_name="exception type")
    exception_message = models.TextField(max_length=10000, verbose_name="exception message")
    traceback = models.TextField(max_length=100000, verbose_name="traceback")
    def __str__(self):
        return "Exception at " + self.path
    class Meta:
        verbose_name = "exception record"
        verbose_name_plural = "exception records"

validation_specifications_for_Upload = {
    'file_type': ('image', 'video'),
    'max_size': {'image': 10485760, 'video': 104857600}, # 10MB, 100MB
    'max_fps': 60,
    # I chose this setting because the production server had difficulty processing a 17 second, 720p, 7MB video without running out of its 512MB memory.
    ## 'max_duration': 10
    'max_duration': 6000 # For development purposes
}
hosting_limits_for_Upload = {
    # When I looked up ext:png on Imgur, all of the images were <1 MB and used PNG correctly. The image should be designed with a computer and have a
    # limited color palette in parts of the photo, not photographed or scanned. This way, using PNG instead of JPG actually shrinks the file size. Not
    # converting to JPG or MP4 will keep solid areas free from artifacts and keep sharp lines from becoming soft. PNG should also be allowed if the
    # file contains transparency and/or lossless animation. Nearly all of the .gif uses on Imgur were for videos, so I decided against allowing .gifs
    # without any transparency.
    'conversion': (('image', 'image/jpeg'), ('image/png', 'image/png', 1048576), ('video', 'video/mp4')),
    'jpeg_quality': 95,
    'max_dimensions': {'image': ((1920,1200),(1080,1920)), 'video': ((1920,1200),(1080,1920))},
    'power_formula_coordinate': (4000000, 1080),
    'high_fps_multiplier': 1.5,
    'reencode_multiplier': 0.75,
    'preset': 'slow',
    # I've tried to make the site as DRY as possible, in that the preceding keys' values can be changed without changing the rest of the site. The
    # site is hard-coded with the assumption that an image or video has a thumbnail if its width is >=600 pixels and that there is a posters directory,
    # although the names of the directories are free to change.
    'thumbnail': ('width', 600, 'thumbnails'),
    'poster_directory': 'posters',
    'exif_directory': 'metadata'
}

class TemporaryUpload(models.Model):
    UPLOAD_TO = "stage2_processing"
    # This model supports the processing stage which occurs after a file is validated. Exceptions are almost unavoidable during this stage, usually due to issues
    # such as the server running out of memory. In that case, there will be files leftover from the processing attempt. Using a separate model makes it easier
    # to keep separate the files and records which can be deleted.
    file = MetadataRestrictedFileField(upload_to=UPLOAD_TO, validation_specifications = validation_specifications_for_Upload, \
                                       storage=CustomStorage(), max_length = 182, verbose_name="file", null=True, blank=True)
    def __str__(self):
        return self.file.name.split('/')[1]

class Upload(models.Model):
    UPLOAD_TO = "uploads"
    
    file = MetadataRestrictedFileField(upload_to=UPLOAD_TO, validation_specifications = validation_specifications_for_Upload, \
                                       storage=CustomStorage(), max_length = 182, verbose_name="file", null=True, blank=True)
    uploader = models.ForeignKey(User, verbose_name="uploader", related_name="uploads", null=True)
    uploader_ip = models.CharField(max_length=45, verbose_name="uploader IP address", default="", blank=True)
    title = models.CharField(max_length=255, verbose_name="title", default="", blank=True)
    # This field is a version of the title with all the spaces replaced by underscores, and possibly including an underscore and seven-character ID from the file name.
    # It was necessary to add this field so that the file could be renamed if the URL existed, because I don't yet know how to query against a function of a field.
    relative_url = models.CharField(max_length=255, verbose_name="relative URL", default="", blank=True)
    description = models.TextField(max_length=10000, verbose_name="description", default="", blank=True)
    source = models.URLField(max_length=250, blank=True, default="")
    is_publicly_listed = models.BooleanField(verbose_name="public?", default=False, blank=True)
    uploader_has_disabled_comments = models.BooleanField(verbose_name="disable comments", default=False, blank=True)
    # Related, relationship-setting models: Comment via upload, Tag via uploads, UserProfile via likes
    def get_category(self):
        try:
            self.adoption
            return "adoption"
        except Adoption.DoesNotExist:
            try:
                self.lost
                return "lost"
            except Lost.DoesNotExist:
                try:
                    self.found
                    return "found"
                except Found.DoesNotExist:
                    return "pets"
    def __str__(self):
        if self.title:
            return self.title
        else:
            # Prevent an error from occurring in the admin site when an administrator tries to look at a record without a title.
            return "Upload #" + str(self.id)

class Metadata(models.Model):
    upload = models.OneToOneField(Upload)
    datetime_uploaded = models.DateTimeField(verbose_name="date and time of upload", auto_now_add=True)
    file_name = models.CharField(max_length=255, verbose_name="file name", default="", blank=True)
    extension = models.CharField(max_length=255, verbose_name="extension", default="", blank=True)
    original_file_name = models.CharField(max_length=255, verbose_name="original file name", default="", blank=True)
    original_extension = models.CharField(max_length=255, verbose_name="original extension", default="", blank=True)
    mime_type = models.CharField(max_length=255, verbose_name="MIME type", default="", blank=True)
    width = models.IntegerField(verbose_name="width", null=True, blank=True)
    height = models.IntegerField(verbose_name="height", null=True, blank=True)
    file_size = models.IntegerField(verbose_name="file size", null=True, blank=True)
    duration = models.FloatField(verbose_name="duration", null=True, blank=True)
    fps = models.FloatField(verbose_name="fps", null=True, blank=True)
    has_audio = models.BooleanField(verbose_name="has audio", default=False, blank=True)
    original_exif_orientation = models.IntegerField(verbose_name="original EXIF orientation", null=True, blank=True)
    def get_geometric_mean(self):
        # If the image or video were a square with the same area, this would be the length of each side. This metric is good for comparing area in a human-readable way.
        return (self.width * self.height) ** (1/2)
    def get_bitrate(self):
        # Return bits per second.
        if self.duration != None:
            return int(self.file_size * 8 / self.duration)
    def __str__(self):
        if self.upload != None and self.upload.relative_url != '':
            return self.upload.relative_url
        else:
            return "Metadata #" + str(self.id)
    class Meta:
        verbose_name = "metadata record"
        verbose_name_plural = "metadata records"

class Tag(models.Model):
    # Tags have their own model in order to be able to sort tags by the number of uploads that are associated with them.
    # Values that have a finite number of choices, like cat breed, do not need their own model because the sorting can be done via a Python function.
    name = models.CharField(max_length=255, verbose_name="name", default="")
    uploads = models.ManyToManyField(Upload, related_name="tags")
    # Other relationship-setting models: UserProfile via subscribers
    def __str__(self):
        return self.name
    # Retrieve up to 20 of the most popular tag names from the database. The output will use the data structure required for a form field's choices argument:
    # a tuple of (value, label) tuples. Each label will be the same as its value. The main upload page uses this.
    def get_popular_tag_names():
        # Retrieve the number of tags to return.
        try:
            number_of_tags = Tag.objects.count()
            if number_of_tags > 20:
                number_of_tags = 20

            tags = Tag.objects.annotate(number_of_uploads=Count('uploads')).order_by("-number_of_uploads")[0:number_of_tags]
            popular_tags = tuple()
            for x in range(number_of_tags):
                popular_tags = popular_tags + ((tags[x].name, tags[x].name),)
            return popular_tags
        except:
            # This exception handles the scenario that the database has been deleted and there is no Tag table to query
            # during migration. Return an empty tuple, the same as when the table exists and there aren't any tags.
            return tuple()

class Like(models.Model):
    # It is necessary to create a record for each like in order to keep track of when each like was made, rather than having it as a profile field.
    # First, this allows the Likes gallery can be sorted by recency, and second, the recency of Likes as votes can be used during ranking algorithms, especially on the front page.
    upload = models.ForeignKey(Upload, verbose_name="upload", related_name="likes")
    liker = models.ForeignKey(User, verbose_name="liker", related_name="likes")
    datetime_liked = models.DateTimeField(verbose_name="date and time of like", auto_now_add=True)
    def __str__(self):
        return self.liker.username + " liked " + self.upload.title

class Comment(models.Model):
    upload = models.ForeignKey(Upload, verbose_name="upload", related_name="comments", null=True)
    last_edited = models.DateTimeField(verbose_name="date and time of last edit", auto_now=True)
    commenter = models.ForeignKey(User, verbose_name="commenter", related_name="comments", null=True, blank=True)
    text = models.TextField(max_length=10000, verbose_name="text", default="")
    def __str__(self):
        return self.text

class UserProfile(models.Model):
    # 1. This section is for authentication information.
    # In views, remember to test for whether the user is logged in before referencing user_profile, or else an exception will occur,
    # as in "if request.user.is_authenticated and request.user.user_profile".
    user_auth = models.OneToOneField(User, related_name="user_profile", primary_key=True)
    registered_with_ip_address = models.CharField(max_length=45, verbose_name="IP address at the time of registration", default="", blank=True)
    # Linked from User, required: username, password, email. Optional: is_active, date_joined, last_login, is_staff, first_name, last_name, get_full_name()
    # 2. This section is for how the user is interacting with uploads and other users.
    following = models.ManyToManyField("self", verbose_name="following", symmetrical=False, related_name="followers", blank=True)
    muting = models.ManyToManyField("self", verbose_name="muting", symmetrical=False, related_name="muters", blank=True)
    subscribed_tags = models.ManyToManyField(Tag, verbose_name="subscribed tags", related_name="subscribers", blank=True)
    # Other relationship-setting models: Upload via uploader, Comment via commenter
    # For Meowseum, UserContactInfo ("user_contact_info") via account, Shelter via account
    def is_shelter(self):
        try:
            self.user_auth.shelter
            return True
        except Shelter.DoesNotExist:
            return False
    def has_contact_information(self):
        # This method is used by the upload_page1.py view, for detecting whether the user needs to be warned, and it is used by the UploadPage1 form for validation.
        # Determine whether the user has contact information on file, either via a UserContact (regular user) or Shelter account record. Only users with account
        # information can upload to the Adoption, Lost, and Found sections.
        try:
           Shelter.objects.get(account = self.user_auth)
           return True
        except Shelter.DoesNotExist:
            try:
                UserContact.objects.get(account = self.user_auth)
                return True
            except UserContact.DoesNotExist:
                return False
    def __str__(self):
        return self.user_auth.username
    class Meta:
        verbose_name = "user profile"
        verbose_name_plural = "user profiles"

class AbuseReport(models.Model):
    ABUSE_TYPE_CHOICES = (('spam, malware, or phishing', 'Spam, malware, phishing'),
                          ('non-cat upload', "Upload isn't a cat"),
                          ('copyright infringement', 'Copyright infringement'),
                          ('sexually explicit', 'Sexually explicit'),
                          ('harassment or threats', 'Harassment/threats'),
                          ('other', 'Other'))
    
    filer = models.ForeignKey(User, verbose_name="filer", related_name="abuse_report", null=True, blank=True)
    type_of_abuse = models.CharField(max_length=255, verbose_name="type of abuse", choices=(('', 'Select a category'),) + ABUSE_TYPE_CHOICES)
    offending_user = models.ForeignKey(User, verbose_name="offending user", related_name="abuse_allegedly_committed", null=True, blank=True)
    description = models.TextField(max_length=100000, verbose_name="description", default="", blank=True)
    url = models.URLField(max_length=255, verbose_name="URL", default="", blank=True)
    # A moderator will change this to True when the abuse report has been read and either action has been taken or action has been declined.
    has_been_processed = models.BooleanField(verbose_name="has been processed?", default=False, blank=True)
    def __str__(self):
        # This format will allow abuse reports to be monitored from the admin module.
        if self.description != '':
            return self.description
        else:
            return self.type_of_abuse.capitalize() + " report #" + str(self.id)
    class Meta:
        verbose_name = "abuse report"
        verbose_name_plural = "abuse reports"

validation_specifications_for_Feedback = {
    'file_type': ('image',),
    'max_size': {'image': 10485760}, # 10MB
}
hosting_limits_for_Feedback = {
    'conversion': (('image', 'image/png'), ('image/jpeg', 'image/jpeg')),
    'jpeg_quality': 95
}
class Feedback(models.Model):
    UPLOAD_TO = "feedback_screenshots"
    
    author = models.ForeignKey(User, verbose_name= "author", related_name="feedback", null=True, blank=True)
    subject = models.CharField(max_length=255, verbose_name="subject")
    comments = models.TextField(max_length=100000, verbose_name="comments")
    email = models.EmailField(max_length=60, verbose_name="email", default="", blank=True)
    screenshot = MetadataRestrictedFileField(upload_to=UPLOAD_TO, validation_specifications = validation_specifications_for_Feedback,\
                                             storage=CustomStorage(), max_length = 182, verbose_name="screenshot", null=True, blank=True)
    def __str__(self):
        return self.subject
    class Meta:
        verbose_name = "feedback record"
        verbose_name_plural = "feedback records"

# The models above this comment are relevant to any social media site. The models below this comment are relevant only to an adoption, lost, or found pet site.

class UserContact(models.Model):
    # This model is for fields modified by the contact information form, for regular users only.
    account = models.OneToOneField(User, related_name="user_contact", null=True)
    address_line_1 = models.CharField(max_length=255, verbose_name="address line 1", default="", blank=True)
    address_line_2 = models.CharField(max_length=255, verbose_name="address line 2", default="", blank=True)
    city = models.CharField(max_length=60, verbose_name="city", default="", blank=True)
    state_or_province = models.CharField(max_length=60, verbose_name="State/Province", choices=(('', 'Select a state'),) + STATE_OR_PROVINCE_CHOICES, default="", blank=True)
    country = models.CharField(max_length=60, verbose_name="country", choices=(('', 'Select a country'),) + COUNTRY_CHOICES, default="", blank=True)
    zip_code = models.CharField(max_length=20, verbose_name="ZIP/Postal Code", default="", blank=True)
    phone_number = models.CharField(max_length=20, verbose_name="phone number", default="", blank=True)
    date_of_birth = models.DateField(verbose_name="date of birth", null=True, blank=True)
    has_volunteering_interest = models.BooleanField(verbose_name="I am interested in volunteering with an animal shelter or rescue group.", default=False, blank=True)
    def __str__(self):
        return self.account.username
    class Meta:
        verbose_name = "contact information record"
        verbose_name_plural = "contact information records"

class Shelter(models.Model):
    SERVICES_INCLUDED_WITH_ADOPTION_FEE_CHOICES = (('spayed or neutered', 'Spaying/neutering'),
    ('vaccinated', 'Vaccinations (up to date)'),
    ('microchipped', 'Microchipping'),
    ('tested and treated for worms, ticks, and fleas', mark_safe('Testing and treatment for worms, ticks, and fleas (<a class="emphasized" href="https://www.aphis.usda.gov/aphis/ourfocus/animalhealth/nvap">USDA</a>-accredited)')))
    
    # Users can apply to create a profile for a shelter or rescue group that is linked to the information they log in with.
    account = models.OneToOneField(User)
    is_verified = models.BooleanField(verbose_name="verified", default=False, blank=True)
    organization_name = models.CharField(max_length=255, verbose_name="organization name", default="")
    contact_first_name = models.CharField(max_length=30, verbose_name="contact first name", default="")
    contact_last_name = models.CharField(max_length=30, verbose_name="contact last name", default="")
    contact_title = models.CharField(max_length=30, verbose_name="contact title", default="", blank=True)
    include_contact_in_profile = models.BooleanField(verbose_name="include contact name in profile", default=False, blank=True)
    # Profile and search engine address
    profile_address_line_1 = models.CharField(max_length=255, verbose_name="profile address line 1", default="", blank=True)
    profile_address_line_2 = models.CharField(max_length=255, verbose_name="profile address line 2", default="", blank=True)
    profile_city = models.CharField(max_length=60, verbose_name="profile city", default="")
    profile_state_or_province = models.CharField(max_length=60, choices=(('', 'Select a state'),) + STATE_OR_PROVINCE_CHOICES, verbose_name="profile state/Province")
    profile_country = models.CharField(max_length=60, choices=(('', 'Select a country'),) + COUNTRY_CHOICES, verbose_name="profile country", default="")
    profile_zip_code = models.CharField(max_length=20, verbose_name="profile ZIP/Postal Code", default="")
    profile_phone_number = models.CharField(max_length=20, verbose_name="profile phone number", default="", blank=True)
    profile_fax_number = models.CharField(max_length=20, verbose_name="profile fax number", default="", blank=True)
    profile_email = models.EmailField(max_length=60, verbose_name="profile email", default="", blank=True)
    website = models.URLField(max_length=255, verbose_name="website", default="", blank=True)
    is_nonprofit = models.BooleanField(verbose_name="status",
                                       help_text="Is your organization governmentally / municipally owned, a 501(c)(3) non-profit, a non-profit exempt from state taxes, \
or a nonprofit with charitable status granted by the Canada Customs and Revenue Agency?",
                                       choices=YES_OR_NO_CHOICES, default=False, blank=True)
    contact_us_page = models.URLField(max_length=255, verbose_name='"Contact Us" page', default="", blank=True)
    donation_page = models.URLField(max_length=255, verbose_name="donation webpage or PayPal link", default="", blank=True)
    # The "other pages" field is more complicated, so I am putting it in later.
    mailing_address_line_1 = models.CharField(max_length=255, verbose_name="mailing address line 1", default="")
    mailing_address_line_2 = models.CharField(max_length=255, verbose_name="mailing address line 2", default="")
    mailing_city = models.CharField(max_length=60, verbose_name="mailing address city", default="")
    mailing_state_or_province = models.CharField(max_length=60, choices=(('', 'Select a state'),) + STATE_OR_PROVINCE_CHOICES, verbose_name="mailing address state/province", default="")
    mailing_country = models.CharField(max_length=60, choices=(('', 'Select a country'),) + COUNTRY_CHOICES, verbose_name="mailing address country", default="")
    mailing_zip_code = models.CharField(max_length=20, verbose_name="mailing address ZIP/Postal Code", default="")
    veterinarian_name = models.CharField(max_length=60, verbose_name="veterinarian name", default="")
    veterinarian_phone_number = models.CharField(max_length=20, verbose_name="veterinarian phone number", default="")
    site_contact_first_name = models.CharField(max_length=30, verbose_name="site contact first name", default="")
    site_contact_last_name = models.CharField(max_length=30, verbose_name="site contact last name", default="")
    site_contact_phone_number = models.CharField(max_length=20, verbose_name="site contact phone number", default="")
    site_contact_email = models.EmailField(max_length=60, verbose_name="site contact email", default="")
    # These fields allow users, while searching, to filter out shelter results that are inapplicable to them.
    distance_prohibition = models.IntegerField(verbose_name="adopters must be within this distance in miles", null=True, blank=True)
    # This field allows specifying a minimum age for adoption, because some shelters set it at 19-21. Because 18 is already implied, 19 is the minimum.
    age_prohibition = models.IntegerField(verbose_name="adopters must be over age", validators=[MinValueValidator(19)], null=True, blank=True)
    is_lost_found_meeting_place = models.BooleanField(verbose_name="Would you like your location to be used as a meeting place when someone has lost a pet and another person has potentially found it?",
                                                      choices=YES_OR_NO_CHOICES, default=False, blank=True)
    # These fields allow skipping parts of the adoption form by automatically filling out the fields that will always be the same.
    base_adoption_fee_cat = models.FloatField(verbose_name="What is your base adoption fee for a cat, age one year or older?", null=True, blank=True)
    base_adoption_fee_kitten = models.FloatField(verbose_name="What is your base adoption fee for a kitten?", null=True, blank=True)
    services_included_with_adoption_fee = ChoiceArrayField(models.CharField(max_length=100, choices=SERVICES_INCLUDED_WITH_ADOPTION_FEE_CHOICES), verbose_name="What services are included with the base adoption fee?", null=True, blank=True)
    def __str__(self):
        return self.organization_name

class PetInfo(models.Model):
    # These are fields shared by adoption, lost, and found uploads. Some of these forms will make more information required than others,
    # so all of the fields use blank=True, and I set which are required in the form instead.
    # Animals of all species use most of the same fields, but with different choices.
    # The labels may also be slightly different. Cats tend to use "hair length" and dogs tend to use "hair length". Most animals other than cats
    # and dogs will use a species dropdown instead of a breed dropdown.
    CAT_BREED_CHOICES = (('Absynnian', 'Absynnian'),
    ('American Bobtail', 'American Bobtail'),
    ('American Curl', 'American Curl'),
    ('American Shorthair', 'American Shorthair'),
    ('American Wirehair', 'American Wirehair'),
    ('Balinese-Javanese', 'Balinese-Javanese'),
    ('Bengal', 'Bengal'),
    ('Birman', 'Birman'),
    ('Bombay', 'Bombay'),
    ('British Shorthair', 'British Shorthair'),
    ('Burmese', 'Burmese'),
    ('Burmilla', 'Burmilla'),
    ('Chartreux', 'Chartreux'),
    ('Colorpoint Shorthair', 'Colorpoint Shorthair'),
    ('Cornish Rex', 'Cornish Rex'),
    ('Cymric', 'Cymric'),
    ('Devon Rex', 'Devon Rex'),
    ('European Burmese', 'European Burmese'),
    ('Exotic Shorthair', 'Exotic Shorthair'),
    ('Havana Brown', 'Havana Brown'),
    ('Himalayan', 'Himalayan'),
    ('Japanese Bobtail', 'Japanese Bobtail'),
    ('Korat', 'Korat'),
    ('Maine Coon', 'Maine Coon'),
    ('LaPerm', 'LaPerm'),
    ('Manx', 'Manx'),
    ('Munchkin', 'Munchkin'),
    ('Nebelung', 'Nebelung'),
    ('Norwegian Forest Cat', 'Norwegian Forest Cat'),
    ('Ocicat', 'Ocicat'),
    ('Oriental', 'Oriental'),
    ('Persian', 'Persian'),
    ('Ragamuffin', 'Ragamuffin'),
    ('Ragdoll', 'Ragdoll'),
    ('Russian Blue', 'Russian Blue'),
    ('Savannah', 'Savannah'),
    ('Scottish Fold', 'Scottish Fold'),
    ('Selkirk Rex', 'Selkirk Rex'),
    ('Siamese', 'Siamese'),
    ('Siberian', 'Siberian'),
    ('Singapura', 'Singapura'),
    ('Snowshoe', 'Snowshoe'),
    ('Somali', 'Somali'),
    ('Sphynx', 'Sphynx'),
    ('Tonkinese', 'Tonkinese'),
    ('Toyger', 'Toyger'),
    ('Turkish Angora', 'Turkish Angora'),
    ('Turkish Van', 'Turkish Van'))
    
    CAT_PATTERN_CHOICES = (('solid', 'Solid color'),
    ('tuxedo', 'Tuxedo'),
    ('Van', 'Van - white with color only on head and tail'),
    ('other bicolor', 'Other bicolor'),
    # Genetics websites and cat fancy sites use "calico" as a subcategory of "tortoiseshell", but some websites use "tortoiseshell" to mean "non-calico", so clarity in the label is important here.
    ('tortoiseshell', 'Multicolor or tortoiseshell'),
    ('tabby stripes', 'Tabby stripes'),
    ('spotted', 'Spotted'))
    IS_CALICO_CHOICES = ((True, 'Calico (has white in its coat)'), (False, 'Non-calico'))
    HAS_TABBY_STRIPES_CHOICES = ((True, 'Yes (also has tabby stripes)'), (False, 'No'))
    IS_DILUTE_CHOICES = ((True, 'Yes (has faded colors)'), (False, 'No'))
    
    CAT_OTHER_PHYSICAL_CHOICES = (('socks', "Has 'socks'"),
                                  ('bobtail', 'Bobtail'),
                                  ('polydactyl', 'Polydactyl (>5 toes)'),
                                  ('heterochromia', 'Heterochromia (each eye differs in color)'))
    CAT_COLOR_CHOICES = (('black', 'Black'),
    ('brown', 'Chocolate or brown'),
    ('gray', 'Gray'),
    ('orange', 'Orange or red'),
    ('tan', 'Tan or buff'),
    ('white', 'White'))
    CAT_DISABILITY_CHOICES = (('visually impaired', 'Visually impaired'),
    ('blind', 'Blind'),
    ('hearing impaired', 'Hearing impaired'),
    ('missing or nonworking limbs', 'Missing or nonworking limbs'),
    ('cerebellar hypoplasia', 'Cerebellar hypoplasia'),
    ('cerebral palsy', 'Cerebral palsy'),
    ('mobility issues', 'Mobility issues'),
    ('mentally disabled', 'Mentally disabled'),
    ('heart problems', 'Heart problems'),
    ('incontinent', 'Incontinent'),
    ('FIV+', 'FIV+'),
    ('leukemia', 'Leukemia'),
    ('diabetic', 'Diabetic'),
    ('obese', 'Obese'),
    ('other', 'Other'))
    AGE_RATING_CHOICES = (('newborn', 'Newborn'), ('young', 'Young'), ('adult', 'Adult'), ('senior', 'Senior'))
    WEIGHT_UNIT_CHOICES = (('lbs', 'lbs'), ('kg', 'kg'))
    AGE_UNIT_CHOICES = (('months', 'months'), ('years', 'years'))
    COAT_LENGTH_CHOICES = (('short', 'Short'), ('medium', 'Medium'), ('long', 'Long'))
    PUBLIC_CONTACT_INFORMATION_CHOICES = (('first name', 'First name'),
    ('last name', 'Last name'),
    ('phone number', 'Phone number'),
    ('email', 'Email'),
    ('address', 'Address'),
    ('city', 'City'),
    ('ZIP code', 'ZIP Code'))
    
    upload = models.OneToOneField(Upload, verbose_name="upload", null=True)
    # The cat has been adopted, returned to its owner, or the owner has contacted the site about taking down the Found post.
    expired = models.BooleanField(verbose_name="expired", default=False, blank=True)
    pet_name = models.CharField(max_length=255, verbose_name="name", default="", blank=True)
    sex = models.CharField(max_length=6, verbose_name="sex", choices=SEX_CHOICES, default="", blank=True)
    subtype1 = models.CharField(max_length=255, verbose_name="breed", choices=(('', 'Select a breed'),) + CAT_BREED_CHOICES, default="", blank=True)
    hair_length = models.CharField(max_length=255, verbose_name="hair length", choices=(('', 'Select a hair length'),) + COAT_LENGTH_CHOICES, default="", blank=True)
    pattern = models.CharField(max_length=255, verbose_name="pattern", choices=(('', 'Select a pattern'),) + CAT_PATTERN_CHOICES, default="", blank=True)
    # The next three fields are displayed instead of color1 and color2 for tortoiseshell (multicolor) cats.
    is_calico = models.NullBooleanField(verbose_name="is calico", choices=((None, ''),) + IS_CALICO_CHOICES, null=True, blank=True)
    has_tabby_stripes = models.NullBooleanField(verbose_name="has tabby stripes", choices=((None, ''),) + HAS_TABBY_STRIPES_CHOICES, null=True, blank=True)
    is_dilute = models.NullBooleanField(verbose_name="is dilute", choices=IS_DILUTE_CHOICES, null=True, blank=True)
    color1 = models.CharField(max_length=255, verbose_name="color 1", choices=(('', 'Pick a color'),) + CAT_COLOR_CHOICES, default="", blank=True)
    # The first color is the one that covers most of the animal's body, and the second color is the one covering a minority of it.
    color2 = models.CharField(max_length=255, verbose_name="color 2", choices=(('', 'Pick a color'),) + CAT_COLOR_CHOICES, default="", blank=True)
    age_rating = models.CharField(max_length=255, verbose_name="approximate age", choices=AGE_RATING_CHOICES, default="", blank=True)
    other_physical = ChoiceArrayField(models.CharField(max_length=100, choices=CAT_OTHER_PHYSICAL_CHOICES), verbose_name="other physical features", blank=True)
    disabilities = ChoiceArrayField(models.CharField(max_length=100, choices=CAT_DISABILITY_CHOICES), verbose_name="disabilities and special needs", blank=True)
    # These fields are included even for lost pets because the Nashville Humane Asssociation's lost/found form has these fields,
    # and Lost notices on animal control sites commonly use a weight range. These fields are targeted toward interacting with shelters.
    weight = models.FloatField(verbose_name="weight", null=True, blank=True)
    weight_units = models.CharField(max_length=255, verbose_name="weight units", choices=(('', ''),) + WEIGHT_UNIT_CHOICES, default="lbs", blank=True)
    precise_age = models.FloatField(verbose_name="age", null=True, blank=True)
    age_units = models.CharField(max_length=255, verbose_name="age units", choices=(('', ''),) + AGE_UNIT_CHOICES, default="months", blank=True)
    public_contact_information = ChoiceArrayField(models.CharField(max_length=100, choices=PUBLIC_CONTACT_INFORMATION_CHOICES), verbose_name="public contact information", blank=True)
    # The only required field for Adoption and Lost is the name. The only required field for Found is whether it is a sighting.
    # These are methods for making it easier to talk about the animal in a sentence.
    def subjective_pronoun(self):
        if self.sex == 'male':
            return 'he'
        elif self.sex == 'female':
            return 'she'
        else:
            return 'it'
    def objective_pronoun(self):
        if self.sex == 'male':
            return 'him'
        elif self.sex == 'female':
            return 'her'
        else:
            return 'it'
    def possessive_pronoun(self):
        if self.sex == 'male':
            return 'his'
        elif self.sex == 'female':
            return 'her'
        else:
            return 'its'
    def absolute_posessive_pronoun(self):
        if self.sex == 'male':
            return 'his'
        elif self.sex == 'female':
            return 'hers'
        else:
            return 'its'
    def reflexive_pronoun(self):
        if self.sex == 'male':
            return 'himself'
        elif self.sex == 'female':
            return 'herself'
        else:
            return 'itself'
    class Meta:
        abstract=True

class Adoption(PetInfo):
    ENERGY_LEVEL_CHOICES = (('low', 'Low'),
    ('average', 'Average'),
    ('active', 'Active'),
    ('very active', 'Very Active'))
    PREFERS_A_HOME_WITHOUT_CHOICES = (('cats', 'Cats'),
    ('dogs', 'Dogs'),
    ('small children', 'Small children'))
    HAS_BEEN_CHOICES = (('spayed or neutered', 'Spayed or neutered'),
    ('house trained', 'House trained'),
    ('declawed', 'Declawed'),
    ('vaccinated', 'Vaccinated (up to date)'),
    ('microchipped', 'Microchipped'),
    ('tested and treated for worms, ticks, and fleas', mark_safe('Tested and treated for worms, ticks, and fleas<span id="accredation-asterisk">*</span><div class="small" id="accredation-footnote">by a <a class="emphasized" href="https://www.aphis.usda.gov/aphis/ourfocus/animalhealth/nvap">USDA</a>-accredited veterinary service</div>')))

    prefers_a_home_without = ChoiceArrayField(models.CharField(max_length=100, choices=PREFERS_A_HOME_WITHOUT_CHOICES), verbose_name="this cat prefers a home without", blank=True)
    has_been = ChoiceArrayField(models.CharField(max_length=100, choices=HAS_BEEN_CHOICES), verbose_name="this cat has been", blank=True)
    energy_level = models.CharField(max_length=255, verbose_name="energy level", choices=(('', 'Select an energy level'),) + ENERGY_LEVEL_CHOICES, default="", blank=True)
    # To fill out the "Bonded with" field, the user will enter the ID used internally by the organization or the relative URL.
    internal_id = models.CharField(max_length=255, verbose_name="pet ID", validators=[RegexValidator(r'^[^,]+$', 'Enter a valid pet ID. This value may not contain commas.')],
                                   unique=True, null=True, blank=True)
    bonded_with = models.ManyToManyField("self", blank=True)
    adoption_fee = models.FloatField(verbose_name="adoption fee", null=True, blank=True)
    euthenasia_soon = models.BooleanField(verbose_name="euthenasia soon", default=False, blank=True)
    def __str__(self):
        return self.pet_name
    class Meta:
        verbose_name = "adoption upload"
        verbose_name_plural = "adoption uploads"

class LostFoundInfo(PetInfo):
    # These fields are common to the Lost and Found categories.
    CAT_EYE_COLOR_CHOICES = (('blue', 'Blue'),
    ('green', 'Green'),
    ('yellow', 'Yellow'),
    ('orange', 'Orange'))
    NOSE_COLOR_CHOICES = (('black', 'Black'),
    ('chocolate or brown', 'Chocolate or brown'),
    ('gray', 'Gray'),
    ('orange', 'Orange or red'),
    ('pink', 'Pink'),
    ('tan', 'Tan or buff'),
    ('white', 'White'))
    # The Lost and Found forms have the yes_or_no_questions field name in common, but not any of the choices.
    COLLAR_COLOR_CHOICES = (('black', 'Black'),
    ('blue', 'Blue'),
    ('brown', 'Brown'),
    ('green', 'Green'),
    ('gray', 'Gray'),
    ('orange', 'Orange'),
    ('multicolor', 'Multicolor'),
    ('pink', 'Pink'),
    ('purple', 'Purple'),
    ('red', 'Red'),
    ('tan', 'Tan'),
    ('yellow', 'Yellow'),
    ('white', 'White'))

    eye_color = models.CharField(max_length=255, verbose_name="eye color", choices=CAT_EYE_COLOR_CHOICES, default="", blank=True)
    eye_color_other = models.CharField(max_length=255, verbose_name="eye color - Other", default="", blank=True)
    nose_color = ChoiceArrayField(models.CharField(max_length=100, choices=NOSE_COLOR_CHOICES), verbose_name="nose color", blank=True)
    date = models.DateField(verbose_name="date", null=True, blank=True)
    location = models.TextField(max_length=10000, verbose_name="location", default="", blank=True)
    other_special_markings = models.TextField(max_length=10000, verbose_name="other special markings", default="", blank=True)
    collar_color = models.CharField(max_length=255, verbose_name="collar color", choices=(('', 'Pick a color'),) + COLLAR_COLOR_CHOICES, default="", blank=True)
    collar_description = models.CharField(max_length=10000, verbose_name="collar description", default="", blank=True)
    class Meta:
        abstract = True

class Lost(LostFoundInfo):
    YES_OR_NO_QUESTIONS_CHOICES = (('has a collar', 'Has a collar'),
    ('microchipped', 'Microchipped'),
    ('has a tattoo of a serial number', 'Has a tattoo of a serial number'),
    ('spayed or neutered', 'Spayed or neutered'),
    ('has a spay or neuter tattoo', 'Has a spay or neuter tattoo'))

    yes_or_no_questions = ChoiceArrayField(models.CharField(max_length=100, choices=YES_OR_NO_QUESTIONS_CHOICES), verbose_name="Which of the following apply to the cat?", blank=True)
    microchip_or_tattoo_ID = models.CharField(max_length=10000, verbose_name="microchip or tattoo ID", default="", blank=True)
    reward = models.FloatField(verbose_name="reward", null=True, blank=True)
    def __str__(self):
        return self.pet_name
    class Meta:
        verbose_name = "lost pet upload"
        verbose_name_plural = "lost pet uploads"

class Found(LostFoundInfo):
    IS_SIGHTING_CHOICES = ((True, "I am reporting that I've seen a lost cat."),
                           (False, "I have the cat in a safe place."))
    YES_OR_NO_QUESTIONS_CHOICES = (('has a collar', 'Has a collar'),
    ('has a spay or neuter tattoo', 'Has a spay or neuter tattoo'),
    ('no microchip detected during scan', 'No microchip detected during scan'))

    is_sighting = models.BooleanField(verbose_name="is a sighting", choices=IS_SIGHTING_CHOICES, default=False, blank=True)
    yes_or_no_questions = ChoiceArrayField(models.CharField(max_length=100, choices=YES_OR_NO_QUESTIONS_CHOICES), verbose_name="Which of the following apply to the cat?", blank=True)
    # This field is for shelters that post pets to the Found section for a few weeks before moving them to the Adoption section
    # and use IDs for those pets, like the pets they have available for adoption.
    internal_id = models.CharField(max_length=255, verbose_name="ID (shelters)", validators=[RegexValidator(r'^[^,]+$', 'Enter a valid pet ID. This value may not contain commas.')],
                                   unique=True, null=True, blank=True)
    def __str__(self):
        return "Found pet #" + self.id
    class Meta:
        verbose_name = "found pet upload"
        verbose_name_plural = "found pet uploads"
