#!/usr/bin/env python
"""
WSGI config for TastyBites project.
"""

import os
import sys

# Add your project directory to Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# Import your Flask app
from app import create_app

# Create the application instance
application = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    application.run()
