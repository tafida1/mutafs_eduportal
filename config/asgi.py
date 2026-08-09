import os
from django.core.asgi import get_asgi_application


django_env = os.getenv("DJANGO_ENV", "production")

if django_env == "development":
    settings_module = "config.settings.development"
else:
    settings_module = "config.settings.production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_asgi_application()