"""
Django settings for Meowseum_Project project.

Generated by 'django-admin startproject' using Django 1.9.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import warnings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v6#(il1xhgv+1^c_46bon=la8f3n3m&9o7uvy8f(oa49s-#a)v'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hitcount',
    'Meowseum',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'Meowseum.middleware.exception_logging_middleware.ExceptionLoggingMiddleware',
    'Meowseum.middleware.user_banning_middleware.LogoutBannedUserMiddleware',
]

ROOT_URLCONF = 'Meowseum_Project.urls'

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'Meowseum/templates')], # Let Django know where to look for templates.
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'Meowseum.context_processors.constant_variables',
                'Meowseum.context_processors.settings_variables',
            ],
        },
    },
]

WSGI_APPLICATION = 'Meowseum_Project.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

warnings.filterwarnings(
    'error', r"DateTimeField .* received a naive datetime",
    RuntimeWarning, r'django\.db\.models\.fields',
)

# Character encoding
DEFAULT_CHARSET='utf-8'

# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
  
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'Meowseum/static/'),
    )
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# User-uploaded files. The first two settings are only used for building a URL based on the file path, so they will contain forward slashes regardless of OS.
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'Meowseum/media/')
# This is the actual path to the /media/ directory, or wherever user-contributed content will be served from.
# For purposes of processing user-uploaded content in both a Windows development environment and a UNIX production environment, store the actual path to the directory.
MEDIA_PATH = MEDIA_ROOT
if os.name == 'nt':
    MEDIA_PATH = MEDIA_PATH.replace('/','\\')

# Settings for CustomStorage.
ALLOW_SPACES = False
ALLOW_NON_UNICODE_ALPHANUMERIC = True

# This block will be used by the custom field MetadataRestrictedFileField for validating files.
# If the file's extension doesn't match that which is preferred for its MIME type, but the file is supported and in the same media category (image or
# video), then the validation program will use these settings to rename the file to a different extension. In common usage, multiple extensions are
# common for the same MIME type, e.g. .jpg and .jpeg for image/jpeg. After renaming, all files with the same MIME type will have the same extension,
# simplifying the relationship from many-to-many to many-to-one.
#
# This variable is used for locating python_magic's data library from the Files for Windows project. It is only used in a Windows environment, but including it here allows
# switching from a Windows development environment to a UNIX production environment more easily. If the OS is UNIX, then it Python Magic uses another file, but the
# program can find its location automatically.
WINDOWS_MAGIC_PATH = r'C:\Program Files (x86)\Python35-32\Lib\site-packages_editable\python-magic\magic_data'
# These extensions are listed alphabetically, except when the extension is a duplicate for the same MIME type. In that case, the extensions are grouped together,
# and the one which I most preferred is listed first. I've included with video-related settings the image extensions and MIME types that can contain
# animated content on the web and that ffmpeg is able to convert to video.
RECOGNIZED_IMAGE_EXTENSIONS = ('.gif', '.jpg', '.jpe', '.jpeg', '.png', '.tif', '.tiff')
RECOGNIZED_VIDEO_EXTENSIONS = ('.gif', '.asf', '.wmv', '.avi', '.flv', '.mkv', '.mov', '.mp4', '.mpg', '.mpeg', '.ogv', '.webm')
# This dictionary should eventually contain all image MIME types that can be handled by the Pillow module and all video MIME types that can be handled
# by ffmpeg, as in whether these programs can convert the file type toward the most common Internet file types. The dictionary is sorted
# alphabetically by file extension within the same general type (image or video). Ffmpeg lists all of their supported formats and codecs, but the list
# isn't available as a list of MIME types. Currently, I have only included the file types I have had time to test. Some extensions have multiple
# possible MIME types. In particular, .mpg uses several different MIME types based on variations in the codec (video/MPV for MPEG-1 or MPEG-2
# Elementary Streams, video/MP2P for MPEG-2 Program Streams), and .3gp (default for Android phone cameras) can be either video/3gpp or audio/3gpp. The
# MIME types should be listed in the official registry at http://www.iana.org/assignments/media-types/media-types.xhtml unless they begin with an x-
# for extension. Some file formats outside the IANA registry have multiple MIME types in usage. For example, people have used .avi has video/x-msvideo
# and video/avi to refer to the same magic number signature. In these cases, I've only included MIME types that are included in Mozilla's list at
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Complete_list_of_MIME_types or returned by python-magic after inputting
# test files.
MIME_TYPES_AND_PREFERRED_EXTENSIONS = {
    'image/gif' : '.gif',
    'image/jpeg': '.jpg',
    'image/png' : '.png',
    'image/tif' : '.tif',
    'video/x-msvideo' : '.avi',
    'video/x-flv' : '.flv',
    'video/x-matroska' : '.mkv',
    'video/quicktime' : '.mov',
    'video/mp4' : '.mp4',
    'video/MP2P' : '.mpg',
    'video/MPV' : '.mpg',
    'video/ogg' : '.ogv',
    'video/webm' : '.webm',
    # UNIX's MediaInfo copy detected a test file as video/x-ms-asf, and Windows's MediaInfo copy detected the same file as video/x-ms-wmv.
    # The latter MIME type is newer. It is for a ASF file that specifically contains bitstreams created by a Windows Media codec. Otherwise, the two file types are identical.
    # I used .asf as the preferred extension because it is always correct, although Microsoft recommends .wmv when .wmv is applicable.
    'video/x-ms-asf': '.asf',
    'video/x-ms-wmv': '.asf'
}
CONVERTIBLE_IMAGE_TYPES = tuple()
CONVERTIBLE_VIDEO_TYPES = ('image/gif',)
for key in MIME_TYPES_AND_PREFERRED_EXTENSIONS:
    if key.startswith('image'):
        CONVERTIBLE_IMAGE_TYPES = CONVERTIBLE_IMAGE_TYPES + (key,)
    else:
        if key.startswith('video'):
            CONVERTIBLE_VIDEO_TYPES = CONVERTIBLE_VIDEO_TYPES + (key,)

JHEAD_PATH = r'C:\Program Files (x86)\Python35-32\Lib\site-packages_editable\jhead.exe'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'database.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# django-hitcount settings
HITCOUNT_HITS_PER_IP_LIMIT = 2000
HITCOUNT_EXCLUDE_USER_GROUP = ('Moderators', )

LOGIN_URL = 'login'
