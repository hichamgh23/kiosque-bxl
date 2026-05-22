from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# ── Sécurité de base ────────────────────────────────────────────────────────
_secret = os.environ.get('SECRET_KEY', '')
if not _secret:
    raise ValueError("SECRET_KEY doit être défini dans le fichier .env")
SECRET_KEY = _secret

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

_hosts = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()]

# En dev, accepte tous les hôtes locaux (mobile sur même réseau Wi-Fi)
if DEBUG:
    ALLOWED_HOSTS += ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware.StealthMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'core.context_processors.cart_info',
                'core.context_processors.support_info',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'fr'
LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
    ('nl', _('Nederlands')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL   = '/static/'
STATIC_ROOT  = BASE_DIR / 'staticfiles'
MEDIA_URL    = '/media/'
MEDIA_ROOT   = BASE_DIR / 'media'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ADMIN_PATH = os.environ.get('ADMIN_PATH', 'bxl-mgmt-9k2z')
LOGIN_URL  = '/admin-kiosque/login/'

# ── Sécurité en production ──────────────────────────────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    X_FRAME_OPTIONS                = 'DENY'
    SECURE_SSL_REDIRECT            = True
    SESSION_COOKIE_SECURE          = True
    SESSION_COOKIE_HTTPONLY        = True
    CSRF_COOKIE_SECURE             = True
    CSRF_COOKIE_HTTPONLY           = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True

# ── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID', '')
