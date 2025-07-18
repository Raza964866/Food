# TastyBites - Food Delivery Platform

A modern food delivery platform built with Flask, featuring user authentication, menu management, order processing, and admin dashboard.

## Project Structure

```
tastybites/                     ← Main project folder
│
├── app/                        ← Main application package
│   ├── __init__.py             ← Flask app factory function
│   ├── models.py               ← SQLAlchemy models
│   ├── routes/                 ← Blueprints for all routes
│   │   ├── __init__.py
│   │   ├── user.py             ← User-facing routes (login, signup, menu, etc.)
│   │   └── admin.py            ← Admin routes (dashboard, menu management)
│   ├── static/                 ← CSS, JS, Images (shared)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/              ← HTML templates (shared)
│   │   ├── layout.html
│   │   ├── login.html
│   │   ├── index.html
│   │   └── ...
│   └── utils/                  ← Helper scripts (e.g., auth, validation)
│       ├── __init__.py
│       └── auth.py
│
├── admin/                      ← Admin-specific module (optional)
│   ├── __init__.py
│   ├── routes.py
│   ├── static/                 ← Admin-specific CSS/JS/images
│   └── templates/              ← Admin-specific HTML templates
│       └── admin/
│           ├── login.html
│           ├── dashboard.html
│           └── ...
│
├── instance/                   ← Holds your SQLite DB (excluded from version control)
│   └── tastybites.db
│
├── config.py                   ← Configuration classes (Development, Production)
├── wsgi.py                     ← WSGI entry point for deployment
├── run.py                      ← Development run script
├── requirements.txt            ← List of Python packages
├── Procfile                    ← Heroku/PythonAnywhere startup command
└── README.md                   ← This file
```

## Features

- **User Authentication**: Registration, login, email verification, password reset
- **Menu Management**: Browse menu items with categories and search
- **Shopping Cart**: Add/remove items, update quantities
- **Order Processing**: Place orders, track order status
- **Admin Dashboard**: Manage users, menu items, and orders
- **Email Integration**: Verification emails and notifications
- **Responsive Design**: Works on desktop and mobile devices

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd tastybites
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=your-database-url
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

5. **Run the application**:
   ```bash
   python run.py
   ```

## Deployment

### PythonAnywhere

1. Upload the project folder to PythonAnywhere
2. Set up a virtual environment and install dependencies
3. Configure the WSGI file to point to `wsgi.py`
4. Set environment variables in the PythonAnywhere dashboard
5. Set up a MySQL database if needed

### Heroku

1. Create a `Procfile` (already included):
   ```
   web: gunicorn wsgi:application
   ```

2. Push to Heroku:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

3. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DATABASE_URL=your-database-url
   ```

## Configuration

The application uses different configurations for different environments:

- **Development**: `config.DevelopmentConfig`
- **Production**: `config.ProductionConfig`
- **Testing**: `config.TestingConfig`

## Database Models

- **User**: User accounts with roles (user/admin)
- **MenuItem**: Food items with categories and pricing
- **Order**: Customer orders with status tracking
- **OrderItem**: Individual items within orders

## API Endpoints

### User Endpoints
- `GET /` - Home page
- `GET /menu` - Menu page
- `POST /login` - User login
- `POST /sign-up` - User registration
- `GET /profile` - User profile
- `POST /place-order` - Place an order

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - Manage users
- `GET /admin/menu` - Manage menu items
- `GET /admin/orders` - Manage orders

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
