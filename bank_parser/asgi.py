"""
ASGI config for bank_parser project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bank_parser.settings')

application = get_asgi_application()
