"""
WSGI config for stock_analysis project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
project_home = os.path.expanduser('~/stock_analysis')
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_analysis.settings')

# Initialize the application
try:
    application = get_wsgi_application()
    print("WSGI application initialized successfully!")
except Exception as e:
    print(f"Error initializing WSGI application: {e}")
    # Re-raise the exception to see it in logs
    raise
