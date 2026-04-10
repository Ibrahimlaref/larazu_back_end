#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brahim.settings')
    settings_module = os.getenv("DJANGO_SETTINGS_MODULE")
    if not settings_module:
        debug = os.getenv("DEBUG", "1").lower() in ("1", "true", "yes", "on")
        settings_module = "brahim.settings.dev" if debug else "brahim.settings.prod"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
