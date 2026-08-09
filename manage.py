import os
import sys


def main():
    django_env = os.getenv("DJANGO_ENV", "development")

    if django_env == "production":
        settings_module = "config.settings.production"
    else:
        settings_module = "config.settings.development"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()