import os
from django.core.wsgi import get_wsgi_application


django_env = os.getenv("DJANGO_ENV", "production")

if django_env == "development":
    settings_module = "config.settings.development"
else:
    settings_module = "config.settings.production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()