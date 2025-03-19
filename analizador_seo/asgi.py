"""
ASGI config for analizador_seo project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analizador_seo.settings')

application = get_asgi_application() 