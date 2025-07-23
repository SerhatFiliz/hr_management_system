import os
from pathlib import Path
from dotenv import load_dotenv
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment Variables ---
# This command finds the .env file in your project's root and loads all the
# variables from it, making them accessible via os.getenv().
load_dotenv() 

# --- Core Security Settings ---

# SECURITY WARNING: keep the secret key used in production secret!
# It's read from the .env file for better security and flexibility.
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# We read the DEBUG value from the .env file. '1' means True, anything else means False.
# This allows you to easily switch between development and production modes.
DEBUG = os.getenv('DEBUG') == '1'

# In a Docker development environment, '*' is often used to allow connections
# from the host machine to the container. For production, you should list
# your actual domain names, e.g., ['yourdomain.com', 'www.yourdomain.com'].
ALLOWED_HOSTS = ['*']


# --- Application Definitions ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'portal',

    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hr_management_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'hr_management_system.wsgi.application'


# --- Database Configuration ---
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # CORRECTED: These variable names now match the ones in our .env file (SQL_DATABASE, SQL_USER, etc.).
        'NAME': os.getenv('SQL_DATABASE'),
        'USER': os.getenv('SQL_USER'),
        'PASSWORD': os.getenv('SQL_PASSWORD'),
        # CRITICAL FOR DOCKER: The 'HOST' is the service name 'db' as defined in docker-compose.yml, not 'localhost'.
        'HOST': os.getenv('SQL_HOST'), 
        'PORT': os.getenv('SQL_PORT'),
    }
}


# --- Password Validation ---
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# --- Internationalization & Timezone ---
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True


# --- Static and Media Files ---
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
# This is where 'collectstatic' will place all static files in production.
STATIC_ROOT = BASE_DIR / 'staticfiles' 

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Authentication URLs ---
LOGIN_REDIRECT_URL = '/portal/dashboard/'
LOGIN_URL = '/accounts/login/'


# --- Crispy Forms Settings ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# --- Celery Configuration ---
# All Celery settings are now read from the .env file for consistency.
# This makes it easy to switch to a different broker (like RabbitMQ) in the future
# by just changing the .env file, without touching the code.
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# --- Celery Beat Scheduler Configuration ---
# This defines all the periodic tasks that Celery Beat should run.
CELERY_BEAT_SCHEDULE = {
    'deactivate-expired-postings-every-day': {
        'task': 'portal.tasks.deactivate_expired_postings',
        # crontab(hour=6, minute=0) means "run every day at 6:00 AM".
        'schedule': crontab(hour=6, minute=0),
    },
}
