"""Check current Django database configuration."""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'

import django
django.setup()
from django.conf import settings

print(f"Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"DB Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"DB Name: {settings.DATABASES['default']['NAME']}")
print(f"DB HOST: {settings.DATABASES['default'].get('HOST', 'N/A')}")
print(f"DB PORT: {settings.DATABASES['default'].get('PORT', 'N/A')}")
print(f"DB USER: {settings.DATABASES['default'].get('USER', 'N/A')}")