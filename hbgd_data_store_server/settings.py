# Copyright 2017-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Django settings for hbgd_data_store_server project.

Generated by 'django-admin startproject' using Django 1.10.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import getpass
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
   pass


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', False)

INTERNAL_IPS = ["127.0.0.1", "localhost", "0.0.0.0"]

DEFAULT_ALLOWED_HOSTS = ','.join(INTERNAL_IPS)

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',')

ADMINS = ()

# Get ADMINS from an env in the format of 'John Doe:johnd@example.com,Jane Doe:janed@example.com'
ADMIN_VARS = os.environ.get('ADMINS', None)
if ADMIN_VARS:
    try:
        for admin in ADMIN_VARS.split(','):
            admin_name, admin_email = admin.split(':')
            ADMINS += ((admin_name, admin_email),)
    except:
        ADMINS = ()

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'debug_toolbar',
    'django_extensions',
    'django_tables2',
    'crispy_forms',
    'crispy_forms_foundation',
    'docs',
    # Local apps
    'studies',
]

DOCS_ROOT = './doc/build/html/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    # 'debug_toolbar.panels.profiling.ProfilingPanel',
]

ROOT_URLCONF = 'hbgd_data_store_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'hbgd_data_store_server.context_processors.export_vars'
            ],
        },
    },
]

WSGI_APPLICATION = 'hbgd_data_store_server.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

if 'RDS_HOSTNAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
    if 'RDS_PASSWORD' in os.environ:
        DATABASES['default']['PASSWORD'] = os.environ.get('RDS_PASSWORD')
elif 'DATABASE_URL' in os.environ:
    url = urlparse(os.environ.get('DATABASE_URL'))
    db_name = url.path.replace('/', '')

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': db_name,
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'hbgd',
            'USER': os.environ.get('DB_USERNAME', getpass.getuser()),
            'PASSWORD': os.environ.get('DB_PASSWORD', None),
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Pacific'

USE_I18N = True

USE_L10N = True

USE_TZ = True


########## STATIC FILE CONFIGURATION
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = os.path.join(BASE_DIR, 'static_files')

# URL prefix for static files.
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static_files/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

################# EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_ADDRESS', 'test@example.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'pass')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_ADDRESS', 'test@example.com')
SERVER_EMAIL = os.environ.get('EMAIL_ADDRESS', 'test@example.com')

################# FILES
FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.TemporaryFileUploadHandler', ]
FILE_UPLOAD_PERMISSIONS = 0o644

################# MISC
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap', 'uni_form', 'bootstrap3', 'foundation-5')
CRISPY_TEMPLATE_PACK = 'foundation-5'

################# DOCS
DOCS_ROOT = os.path.join(BASE_DIR, 'docs/build/html')
DOCS_ACCESS = 'staff'

#################  Google Analytics
GTM_CONTAINER_ID = os.environ.get('GTM_CONTAINER_ID', None)
