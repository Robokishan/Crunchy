import os
from pathlib import Path
from decouple import config as DefaultConfig
from decouple import Config, RepositoryEnv

DEV_ENV_FILE = "../.env.dev"
PROD_ENV_FILE = "../.env.prod"

# default env file
DOTENV_FILE = os.environ.get("DOTENV_FILE", DEV_ENV_FILE)

config: Config = DefaultConfig

ENVIORNMENT = os.environ.get('PYTHON_ENV', "dev")

if ENVIORNMENT == "dev":
    config = Config(RepositoryEnv(DEV_ENV_FILE))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool, default=False)

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
    'knowledgeGraph'
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
                'host': config('MONGODB_URL', cast=str),
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
KAFKA_USERNAME = config('KAFKA_USERNAME', cast=str)
KAFKA_PASSWORD = config('KAFKA_PASSWORD', cast=str)
KAFKA_SERVER = config('KAFKA_SERVER', cast=str)
KAFKA_SASL_MECHANISM = config('KAFKA_SASL_MECHANISM', cast=str)
KAFKA_GROUP_ID = config('KAFKA_GROUP_ID', cast=str)
KAFKA_CRUNCHBASE_DATABUCKET_TOPIC = config(
    'KAFKA_CRUNCHBASE_DATABUCKET_TOPIC', cast=str)

# rabbitMQ
RABBITMQ_URL = config('RABBITMQ_URL', cast=str)
RB_MAIN_EXCHANGE = config('RABBIT_MQ_MAIN_EXCHANGE', cast=str)
RB_MAIN_ROUTING_KEY = config('RABBIT_MQ_MAIN_ROUTING_KEY', cast=str)
RB_MAIN_QUEUE = config('RABBIT_MQ_MAIN_QUEUE', cast=str)
