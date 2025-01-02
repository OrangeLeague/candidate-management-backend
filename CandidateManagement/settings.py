"""
Django settings for CandidateManagement project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import dj_database_url
import os

# Determine the environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # Default to 'development'

# Debug mode
# DEBUG = ENVIRONMENT != 'production'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-2kyyi3*0u@kgkc%%g398ul&12-%%8y41oqhxzim0rimk86ojk5"

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = False


ALLOWED_HOSTS = ['127.0.0.1','localhost','olvtechnologies-cms.onrender.com','candidate-management-backend-1.onrender.com']


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "candidates",
    "corsheaders",
    "rest_framework",
    "whitenoise.runserver_nostatic",
    "whitenoise"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = "CandidateManagement.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "CandidateManagement.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if ENVIRONMENT=='production':
    # Production settings
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        "default": {
            'ENGINE': 'django.db.backends.postgresql',  # Use PostgreSQL
            # 'NAME': 'postgres',                     # Your database name
            'NAME':'olvtdb',
            # 'USER': 'postgres',                         # Your database username
            'USER':'olvtdb_user',
            # 'PASSWORD': 'postgres',                 # Your database password
            'PASSWORD':'meU7gCaUjdYnv3u4GIJOpUxZAJAuo77k',
            # 'HOST': 'localhost',                      # Host address (localhost for local)
            'HOST':'dpg-ctbf02jtq21c73c5o3dg-a.oregon-postgres.render.com',
            'PORT': '5432', 
        }
    }

print(f"Running in {ENVIRONMENT} mode. DEBUG is {'ON' if DEBUG else 'OFF'}")

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / 'staticfiles'

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LOGIN_URL = '/admin/login/'

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Default session engine
SESSION_COOKIE_SECURE = True  # For local testing; set True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
# SESSION_COOKIE_SAMESITE='None'
SESSION_COOKIE_NAME = 'sessionid'  # Default cookie name

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://olvtechnologies-cms.netlify.app",  # Your frontend URL
    "http://localhost:3000",  # For local development
    "https://candidate-management-backend-1.onrender.com"
]

CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',  # The URL of your React frontend
]

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week

SESSION_COOKIE_NAME = 'sessionid'  # Default session cookie name

CSRF_TRUSTED_ORIGINS = ['http://localhost:3000','http://localhost:8000','https://olvtechnologies-cms.netlify.app',"https://candidate-management-backend-1.onrender.com","https://olvtechnologies-cms.netlify.app"]

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# settings.py

BACKBLAZE_ACCESS_KEY = "0055220d59da28e0000000001"  # keyID
BACKBLAZE_SECRET_KEY = "K0051GxUfvsAzESLv33K9AulaV+nd1E"  # applicationKey
BACKBLAZE_ENDPOINT_URL = "https://s3.us-east-005.backblazeb2.com"  # Adjust if region is us-east-005
BACKBLAZE_BUCKET_NAME = "OLVT-DB"



# AWS S3 Configuration in Django settings.py

AWS_ACCESS_KEY_ID = 'AKIAS2VS4NCUU2RN32G4'  # Replace with your AWS Access Key ID
AWS_SECRET_ACCESS_KEY = '3hxcTp4+roOW7YZtIzZnZO45phCX3ZzXnNskv6pz'  # Replace with your AWS Secret Access Key
AWS_STORAGE_BUCKET_NAME = 'olvttalentspherebucket'  # Replace with your bucket name
AWS_S3_REGION_NAME = 'ap-south-1'  # e.g., 'us-west-2'
AWS_S3_ENDPOINT_URL = 'https://s3.amazonaws.com'  # Default S3 endpoint URL

# Optional: Custom domain for S3 (if you're using one)
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# Static and media files settings
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
