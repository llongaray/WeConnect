import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-inseguro-trocar-em-producao')
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,host.docker.internal').split(',')

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'channels',
    'apps.accounts',
    'apps.whatsapp',
    'apps.chat',
    'apps.platform_chat',
    'apps.automation',
    'apps.integrations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.accounts.middleware.ApiCsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.accounts.middleware.ActiveAccountMiddleware',
    'apps.accounts.middleware.PrivacyAcceptanceGateMiddleware',
    'apps.accounts.middleware.TotpSetupGateMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'weconnect.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'weconnect.wsgi.application'
ASGI_APPLICATION = 'weconnect.asgi.application'

if os.getenv('POSTGRES_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': os.getenv('POSTGRES_HOST', 'postgres-app'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'NAME': os.getenv('POSTGRES_DB', 'moneyconnect'),
            'USER': os.getenv('POSTGRES_USER', 'moneyconnect'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'moneyconnect_pass'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache Redis (segurança / rate limit / anti-bruteforce)
_redis_cache_url = os.getenv(
    'REDIS_CACHE_URL',
    f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:6379/3" if os.getenv('REDIS_HOST') else '',
)
if _redis_cache_url:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_cache_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'weconnect-security',
        },
    }

# Anti-bruteforce login (documentação — lido em login_security.py)
LOGIN_MAX_ATTEMPTS = int(os.getenv('LOGIN_MAX_ATTEMPTS', '5'))
LOGIN_ATTEMPT_WINDOW_MINUTES = int(os.getenv('LOGIN_ATTEMPT_WINDOW_MINUTES', '15'))
LOGIN_LOCKOUT_MINUTES = int(os.getenv('LOGIN_LOCKOUT_MINUTES', '30'))

CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173',
).split(',')
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.CookieJWTAuthentication',
        *(
            ('rest_framework_simplejwt.authentication.JWTAuthentication',)
            if DEBUG
            else ()
        ),
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('API_RATE_LIMIT_ANON', '30/min'),
        'user': os.getenv('API_RATE_LIMIT_USER', '120/min'),
        'auth': os.getenv('AUTH_RATE_LIMIT', '10/min'),
        'cnpj_lookup': os.getenv('CNPJ_LOOKUP_RATE_LIMIT', '20/min'),
        'deepseek': os.getenv('DEEPSEEK_RATE_LIMIT', '10/min'),
    },
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_MINUTES', '30'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

JWT_ACCESS_COOKIE_NAME = os.getenv('JWT_ACCESS_COOKIE_NAME', 'wc_access')
JWT_REFRESH_COOKIE_NAME = os.getenv('JWT_REFRESH_COOKIE_NAME', 'wc_refresh')
TRUSTED_DEVICE_COOKIE_NAME = os.getenv('TRUSTED_DEVICE_COOKIE_NAME', 'wc_trusted')
TRUSTED_DEVICE_DAYS = int(os.getenv('TRUSTED_DEVICE_DAYS', '30'))

# Cloudflare Turnstile (CAPTCHA gratuito)
TURNSTILE_SITE_KEY = os.getenv('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.getenv('TURNSTILE_SECRET_KEY', '')

# Admin Django — desabilitar em produção se ADMIN_ENABLED=false
ADMIN_ENABLED = os.getenv('ADMIN_ENABLED', 'true').lower() == 'true'

USE_REDIS_CHANNELS = os.getenv('USE_REDIS_CHANNELS', '').lower() == 'true'

CHANNEL_LAYERS = {
    'default': {
        # Em dev local, memória evita conflito com o Redis da Evolution API
        'BACKEND': (
            'channels_redis.core.RedisChannelLayer'
            if USE_REDIS_CHANNELS or not DEBUG
            else 'channels.layers.InMemoryChannelLayer'
        ),
        **(
            {
                'CONFIG': {
                    'hosts': [os.getenv(
                        'REDIS_CHANNELS_URL',
                        f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:6379/2",
                    )],
                },
            }
            if USE_REDIS_CHANNELS or not DEBUG
            else {}
        ),
    },
}

USE_CELERY = os.getenv('USE_CELERY', '').lower() == 'true'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_ROUTES = {
    'weconnect.process_chatbot': {'queue': 'automation'},
    'weconnect.ping': {'queue': 'default'},
    'accounts.purge_security_events': {'queue': 'maintenance'},
    'accounts.purge_audit_logs': {'queue': 'maintenance'},
    'chat.purge_expired_data': {'queue': 'maintenance'},
}

CELERY_BEAT_SCHEDULE = {
    'purge-security-events-weekly': {
        'task': 'accounts.purge_security_events',
        'schedule': 60 * 60 * 24 * 7,
        'kwargs': {'days': 90},
    },
    'purge-chat-data-daily': {
        'task': 'chat.purge_expired_data',
        'schedule': 60 * 60 * 24,
    },
    'purge-audit-logs-monthly': {
        'task': 'accounts.purge_audit_logs',
        'schedule': 60 * 60 * 24 * 30,
        'kwargs': {'days': 365},
    },
}

# Evolution API
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', 'mude-me-para-uma-chave-segura')
EVOLUTION_WEBHOOK_BASE_URL = os.getenv(
    'EVOLUTION_WEBHOOK_BASE_URL',
    'http://host.docker.internal:8000/api/webhooks',
)

# Meta Cloud API (OAuth na fase 2)
META_APP_ID = os.getenv('META_APP_ID', '')
META_APP_SECRET = os.getenv('META_APP_SECRET', '')
META_GRAPH_API_VERSION = os.getenv('META_GRAPH_API_VERSION', 'v21.0')

# Limite de upload de mídia (16 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DATA_UPLOAD_MAX_MB', '100')) * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('FILE_UPLOAD_MAX_MB', '100')) * 1024 * 1024

# DeepSeek API
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_DASHBOARD_MODEL = os.getenv('DEEPSEEK_DASHBOARD_MODEL', 'deepseek-reasoner')

# OpenAI / ChatGPT
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# Anthropic / Claude
ANTHROPIC_BASE_URL = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
ANTHROPIC_API_VERSION = os.getenv('ANTHROPIC_API_VERSION', '2023-06-01')

# Google Gemini
GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

# Timeout compartilhado entre provedores de IA
AI_TIMEOUT = int(os.getenv('AI_TIMEOUT', os.getenv('DEEPSEEK_TIMEOUT', '120')))
DEEPSEEK_TIMEOUT = AI_TIMEOUT

# Alertas de segurança (webhook Discord/Slack gratuito)
SECURITY_ALERT_WEBHOOK_URL = os.getenv('SECURITY_ALERT_WEBHOOK_URL', '')

# 2FA — papéis obrigados a configurar TOTP
TOTP_REQUIRED_ROLES = os.getenv('TOTP_REQUIRED_ROLES', 'superuser,gestor')

# CSRF cookie legível pelo frontend (double-submit)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security_json': {
            'format': '{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        },
    },
    'handlers': {
        'security_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'security_json',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Headers de segurança em produção
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    _hsts = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
    if _hsts > 0:
        SECURE_HSTS_SECONDS = _hsts
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Fail-fast em produção — evita defaults inseguros
if not DEBUG:
    from django.core.exceptions import ImproperlyConfigured

    if SECRET_KEY == 'dev-inseguro-trocar-em-producao':
        raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY seguro em produção.')
    if not _redis_cache_url:
        raise ImproperlyConfigured('REDIS_CACHE_URL é obrigatório em produção (rate limit distribuído).')
    if EVOLUTION_API_KEY == 'mude-me-para-uma-chave-segura':
        raise ImproperlyConfigured('Defina EVOLUTION_API_KEY segura em produção.')
    if not os.getenv('FIELD_ENCRYPTION_KEY'):
        raise ImproperlyConfigured('FIELD_ENCRYPTION_KEY é obrigatória em produção.')
