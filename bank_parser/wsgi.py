"""
WSGI config for bank_parser project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bank_parser.settings')

application = get_wsgi_application()
