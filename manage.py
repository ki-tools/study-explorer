#!/usr/bin/env python
import os
import sys
from os import path

PROJECT_ROOT = path.abspath(path.dirname(__file__))
SETTINGS_DIR = path.abspath(path.join(PROJECT_ROOT, 'hbgd_data_store_server'))
if __name__ == "__main__":
    sys.path.append(SETTINGS_DIR)
    if 'TRAVIS' in os.environ:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hbgd_data_store_server.settings_travis")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hbgd_data_store_server.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    if sys.argv[1] == 'test':
        import pytest
        sys.exit(pytest.main(sys.argv[2:]))
    else:
        execute_from_command_line(sys.argv)
