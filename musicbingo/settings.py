from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# Carga el .env
load_dotenv()

# Fallback solo si no hay .env (desarrollo local sin archivo)
SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-temporal-solo-desarrollo-no-usar-en-prod')

#normal
BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ FIX: Sin fallback hardcodeado — si falta la variable, Django falla explicitamente
SECRET_KEY = os.environ['SECRET_KEY']

# En tu .env local pon: DEBUG=True
# En Render pon: DEBUG=False
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'bingo',
]

ASGI_APPLICATION = 'musicbingo.asgi.application'

# ✅ MEJORA: Redis en produccion, memoria en local
# En Render agrega la variable REDIS_URL con tu instancia Redis
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ AÑADIR para archivos estaticos en produccion
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'musicbingo.urls'

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

WSGI_APPLICATION = 'musicbingo.wsgi.application'

# ✅ FIX PRINCIPAL: ssl_require depende del entorno
# En local (sin DATABASE_URL en .env) usa el string por defecto SIN ssl
# En Render (con DATABASE_URL) dj_database_url lo maneja automaticamente
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Produccion en Render: Render ya incluye sslmode en la URL
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Desarrollo local: sin SSL, sin credenciales en el codigo
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'bingomusic-postgres'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5433'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # ✅ Necesario para collectstatic en Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'ver_mi_carton'

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'