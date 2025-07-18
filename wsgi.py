#!/usr/bin/env python
"""
WSGI entry point for PythonAnywhere deployment
"""

import os
import sys

# Add your project directory to Python path
path = '/home/yourusername/Food'  # You'll need to update this path
if path not in sys.path:
    sys.path.insert(0, path)

from app import create_app

# Create the application instance
application = create_app('production')

if __name__ == "__main__":
    application.run()
