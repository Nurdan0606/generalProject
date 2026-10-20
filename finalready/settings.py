import os
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / '.env'
load_dotenv(ENV_FILE)
LOCAL_ENV = dotenv_values(ENV_FILE)
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'local-development-only-change-before-deployment')
if not DEBUG and SECRET_KEY == 'local-development-only-change-before-deployment':
    raise RuntimeError('Set DJANGO_SECRET_KEY for production.')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
                  'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'study']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
              'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
              'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
              'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'finalready.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
              'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request',
              'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'finalready.wsgi.application'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('POSTGRES_DB', 'finalready'),
    'USER': os.getenv('POSTGRES_USER', 'finalready'),
    'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
    'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'PORT': os.getenv('POSTGRES_PORT', '5432'),
    'OPTIONS': {'connect_timeout': 5},
}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.' + name} for name in
    ['UserAttributeSimilarityValidator', 'MinimumLengthValidator', 'CommonPasswordValidator', 'NumericPasswordValidator']]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Qyzylorda'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
# Prefer explicit project-local OpenAI settings so a stale user-level key cannot
# silently override the key the developer just placed in this project's .env.
OPENAI_API_KEY = LOCAL_ENV.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = LOCAL_ENV.get('OPENAI_MODEL') or os.getenv('OPENAI_MODEL', 'gpt-6-luna')
OPENAI_TIMEOUT_SECONDS = int(
    LOCAL_ENV.get('OPENAI_TIMEOUT_SECONDS') or os.getenv('OPENAI_TIMEOUT_SECONDS', '180')
)
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
SESSION_COOKIE_HTTPONLY = True
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
