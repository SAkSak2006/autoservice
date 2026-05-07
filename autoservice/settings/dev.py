from .base import *  # noqa: F401, F403

DEBUG = True

# PostgreSQL via Docker (docker compose up -d db)
# DATABASE_URL from .env: postgres://autoservice:autoservice@localhost:5432/autoservice_db

INSTALLED_APPS += [  # noqa: F405
    'debug_toolbar',
]

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405

INTERNAL_IPS = ['127.0.0.1']

# Email: use Resend if API key is set, otherwise console
RESEND_API_KEY = env('RESEND_API_KEY', default='')  # noqa: F405
if RESEND_API_KEY:
    EMAIL_BACKEND = 'notifications.email_backend.ResendEmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Simplified static files for dev
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
