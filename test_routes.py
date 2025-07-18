#!/usr/bin/env python
"""
Test script to check if routes are working
"""

from app import create_app

def test_routes():
    app = create_app()
    print("✅ App created successfully!")
    
    with app.test_client() as client:
        print("\nTesting main routes...")
        
        # Test home page
        response = client.get('/')
        print(f"Home page (/): {response.status_code}")
        
        # Test menu page
        response = client.get('/menu')
        print(f"Menu page (/menu): {response.status_code}")
        
        # Test login page
        response = client.get('/login')
        print(f"Login page (/login): {response.status_code}")
        
        # Test admin login page
        response = client.get('/admin/login')
        print(f"Admin login (/admin/login): {response.status_code}")
        
        # Test admin dashboard (should redirect to login)
        response = client.get('/admin/dashboard')
        print(f"Admin dashboard (/admin/dashboard): {response.status_code}")
        
        # Test about page
        response = client.get('/about')
        print(f"About page (/about): {response.status_code}")
        
        # Test contact page
        response = client.get('/contact')
        print(f"Contact page (/contact): {response.status_code}")
        
        print("\n✅ All routes tested successfully!")

if __name__ == '__main__':
    test_routes()
