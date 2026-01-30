"""
WSGI config for empmanager project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')

application = get_wsgi_application()
