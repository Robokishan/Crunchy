import os
from pathlib import Path

DEV_ENV_FILE = "../.env.dev"
PROD_ENV_FILE = "../.env.prod"

# default env file
DOTENV_FILE = os.environ.get("DOTENV_FILE", DEV_ENV_FILE)

ENVIORNMENT = os.environ.get('PYTHON_ENV', "dev")


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = 'abcd'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*', 'crunchy_api:8000']
# If this is used then `CORS_ALLOWED_ORIGINS` will not have any effect
CORS_ALLOW_ALL_ORIGINS = True


# Application definition

INSTALLED_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    # Django REST framework
    'kafka',
    'databucket',
    'public',
    'rabbitmq',
    'api',
    'knowledgeGraph',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CrunchyRest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CrunchyRest.wsgi.application'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'crunchy',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
                'host': 'mongodb://localhost:27017/crunchy',
        },
        'LOGGING': {
            'version': 1,
            'loggers': {
                'djongo': {
                    'level': 'DEBUG',
                    'propagate': False,
                }
            },
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# KAFKA SETTINGS
KAFKA_USERNAME = 'KAFKA_USERNAME'
KAFKA_PASSWORD = 'KAFKA_PASSWORD'
KAFKA_SERVER = 'KAFKA_SERVER'
KAFKA_SASL_MECHANISM = 'KAFKA_SASL_MECHANISM'
KAFKA_GROUP_ID = 'KAFKA_GROUP_ID'
KAFKA_CRUNCHBASE_DATABUCKET_TOPIC = 'KAFKA_CRUNCHBASE_DATABUCKET_TOPIC'

# rabbitMQ
RABBITMQ_URL = None
RB_MAIN_EXCHANGE = 'RABBIT_MQ_MAIN_EXCHANGE'
RB_MAIN_ROUTING_KEY = 'RABBIT_MQ_MAIN_ROUTING_KEY'
RB_MAIN_QUEUE = 'RABBIT_MQ_MAIN_QUEUE'

# priority rabbitmq queue
RABBIT_MQ_PRIORITY_EXCHANGE = 'RABBIT_MQ_PRIORITY_EXCHANGE'
RABBIT_MQ_PRIORITY_ROUTING_KEY = 'RABBIT_MQ_PRIORITY_ROUTING_KEY'
RABBIT_MQ_PRIORITY_QUEUE = 'RABBIT_MQ_PRIORITY_QUEUE'

NEO4J_RESOURCE_URI = None
NEO4J_USERNAME = 'NEO4J_USERNAME'
NEO4J_PASSWORD = 'NEO4J_PASSWORD'
