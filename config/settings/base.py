from pathlib import Path
from decouple import config
import environ
import os
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

environ.Env.read_env(
    os.path.join(BASE_DIR, ".env")
)

SECRET_KEY = config("SECRET_KEY", default="unsafe-dev-secret-key-change-in-production")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=lambda v: [s.strip() for s in v.split(",")]
)

INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "widget_tweaks",
    "django_filters",
    "ckeditor",
    "ckeditor_uploader",

    # Local apps
    "apps.accounts",
    "apps.schools",
    "apps.academics",
    "apps.students",
    "apps.parents",
    "apps.staffs",
    "apps.attendance",
    "apps.results",
    "apps.cbt",
    "apps.lessons",
    "apps.timetable",
    "apps.finance",
    "apps.notifications",
    "apps.analytics",
    "apps.audit",
    "apps.public_portal",
    "apps.profiles",
    "apps.backups",
    "apps.messaging",
    "apps.intelligence",
    "apps.data_tools",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.schools.tenant_middleware.TenantMaintenanceMiddleware",
    "apps.accounts.middleware.ForcePasswordChangeMiddleware",

    # Custom SaaS middleware
    "apps.core.middleware.SchoolStatusMiddleware",
    "apps.core.middleware.SubscriptionMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.schools.middleware.SubscriptionMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",

                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "apps.core.context_processors.global_context",
                "apps.notifications.context_processors.notification_context",
                "apps.messaging.context_processors.unread_messages_count",
                "apps.schools.context_processors.tenant_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard_router"
LOGOUT_REDIRECT_URL = "login"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

CKEDITOR_UPLOAD_PATH = "cbt_uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False

X_FRAME_OPTIONS = "DENY"

SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")


OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_MODEL = env("OPENAI_MODEL", default="gpt-4.1-mini")



PAYSTACK_SECRET_KEY = env(
    "PAYSTACK_SECRET_KEY",
    default="",
)

PAYSTACK_PUBLIC_KEY = env(
    "PAYSTACK_PUBLIC_KEY",
    default="",
)

PAYSTACK_CALLBACK_URL = env(
    "PAYSTACK_CALLBACK_URL",
    default="http://127.0.0.1:8000/finance/payments/verify/",
)




CACHE_TTL = 60 * 5  # 5 minutes

CACHES = {
    "default": {
        "BACKEND": config(
            "CACHE_BACKEND",
            default="django.core.cache.backends.locmem.LocMemCache",
        ),
        "LOCATION": config(
            "CACHE_LOCATION",
            default="mutafs-eduportal-cache",
        ),
    }
}



DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Mutafs EduPortal <noreply@mutafs.com>",
)



DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

SESSION_COOKIE_AGE = 60 * 60 * 4
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

PASSWORD_RESET_TIMEOUT = 60 * 60