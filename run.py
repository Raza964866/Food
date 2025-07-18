#!/usr/bin/env python
"""
Development run script for TastyBites
"""

import os
from app import create_app

if __name__ == '__main__':
    # Create the app
    app = create_app('development')
    
    print("TastyBites is running at http://127.0.0.1:5000/")
    print("Press Ctrl+C to stop the server")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
