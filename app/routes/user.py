# User routes
from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
from .. import db
from ..models import MenuItem, Order, OrderItem, User
from ..utils.auth import generate_reset_token, verify_reset_token
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from .. import mail
import random
import string
from functools import wraps

# Create a Blueprint for the routes
user_bp = Blueprint('user', __name__)

# Menu routes
@user_bp.route('/api/menu')
def get_menu():
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    items = [{
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'price': item.price,
        'category': item.category,
        'image': item.image
    } for item in menu_items]
    return jsonify(items)

# Cart routes
@user_bp.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    
    # Initialize cart if it doesn't exist in session
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if item already in cart
    item_id = data.get('id')
    item_exists = False
    
    for item in session['cart']:
        if item['id'] == item_id:
            item['quantity'] += 1
            item_exists = True
            break
    
    # If item not in cart, add it
    if not item_exists:
        session['cart'].append({
            'id': item_id,
            'name': data.get('name'),
            'price': data.get('price'),
            'quantity': 1
        })
    
    # Save session
    session.modified = True
    
    return jsonify({'success': True, 'cart': session['cart']})

@user_bp.route('/api/cart/update', methods=['POST'])
def update_cart():
    data = request.json
    item_id = data.get('id')
    quantity = data.get('quantity')
    
    if 'cart' in session:
        for item in session['cart']:
            if item['id'] == item_id:
                item['quantity'] = quantity
                if quantity <= 0:
                    session['cart'].remove(item)
                break
        
        session.modified = True
    
    return jsonify({'success': True, 'cart': session.get('cart', [])})

@user_bp.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    item_id = data.get('id')
    
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != item_id]
        session.modified = True
    
    return jsonify({'success': True, 'cart': session.get('cart', [])})

@user_bp.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    if 'cart' in session:
        session.pop('cart')
    
    return jsonify({'success': True})

@user_bp.route('/api/cart')
def get_cart():
    return jsonify({'cart': session.get('cart', [])})

@user_bp.route('/api/cart/save', methods=['POST'])
def save_cart():
    try:
        data = request.get_json()
        if not data or 'cart' not in data:
            return jsonify({'success': False, 'message': 'No cart data provided'}), 400
            
        # Save cart to session
        session['cart'] = data['cart']
        return jsonify({'success': True, 'message': 'Cart saved successfully'})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving cart: {str(e)}'
        }), 500

# Order routes
@user_bp.route('/api/order/create', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        if not data:
            print("[DEBUG] No data provided in order creation request.")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        items = data.get('items', [])
        if not items:
            print("[DEBUG] No items in order creation request.")
            return jsonify({'success': False, 'message': 'No items in order'}), 400
        
        print(f"[DEBUG] Received order request with {len(items)} items.")
        
        # Calculate total amount and validate items
        total_amount = 0
        order_items = []
        
        for item in items:
            try:
                menu_item = MenuItem.query.get(item['id'])
                if not menu_item:
                    print(f"[DEBUG] Menu item {item['id']} not found.")
                    return jsonify({'success': False, 'message': f'Menu item {item["id"]} not found'}), 404
                    
                quantity = int(item.get('quantity', 1))
                if quantity < 1:
                    print(f"[DEBUG] Invalid quantity for item {item['id']}: {quantity}")
                    return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
                    
                price = float(item.get('price', 0))
                if price <= 0:
                    print(f"[DEBUG] Invalid price for item {item['id']}: {price}")
                    return jsonify({'success': False, 'message': 'Invalid price'}), 400
                    
                total_amount += price * quantity
                
                order_items.append({
                    'menu_item_id': menu_item.id,
                    'quantity': quantity,
                    'price': price,
                    'name': menu_item.name
                })
                print(f"[DEBUG] Validated item: {menu_item.name} (ID: {menu_item.id}, Qty: {quantity}, Price: {price})")
                
            except (KeyError, ValueError) as e:
                print(f"[ERROR] Invalid item data in order request: {str(e)}")
                return jsonify({'success': False, 'message': f'Invalid item data: {str(e)}'}), 400
        
        # Update user information if provided in the form
        user_name = data.get('name')
        user_email = data.get('email')
        user_phone = data.get('phone')
        user_address = data.get('address')
        
        if user_name and user_name.strip():
            current_user.name = user_name.strip()
        if user_email and user_email.strip():
            current_user.email = user_email.strip()
        if user_phone and user_phone.strip():
            current_user.phone = user_phone.strip()
        if user_address and user_address.strip():
            current_user.address = user_address.strip()
        
        # Create new order
        new_order = Order(
            user_id=current_user.id,
            order_date=datetime.utcnow(),
            status='Pending',
            total_amount=total_amount,
            delivery_address=user_address,
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get the order ID without committing
        print(f"[DEBUG] New order created with ID: {new_order.id}")
        
        # Create order items
        for item in data['items']:
            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
            print(f"[DEBUG] Added order item: {item['name']} (Qty: {item['quantity']})")
        
        # Clear the user's cart after successful order
        if 'cart' in session:
            session.pop('cart')
            print("[DEBUG] User's cart cleared from session.")
        
        # Commit all changes
        db.session.commit()
        print("[DEBUG] Order and order items committed to database.")
        
        return jsonify({
            'success': True, 
            'order_id': new_order.id,
            'message': 'Order placed successfully',
            'redirect': f'/receipt/{new_order.id}'
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[ERROR] Error creating order: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while placing your order. Please try again.'
        }), 500

@user_bp.route('/api/orders')
@login_required
def get_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    
    orders_list = [{
        'id': order.id,
        'date': order.order_date.strftime('%Y-%m-%d %H:%M'),
        'status': order.status,
        'total': order.total_amount
    } for order in orders]
    
    return jsonify(orders_list)

@user_bp.route('/api/orders/<int:order_id>')
@login_required
def get_order_details(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    
    items = []
    for item in order_items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        items.append({
            'id': item.id,
            'name': menu_item.name,
            'quantity': item.quantity,
            'price': item.price,
            'total': item.price * item.quantity
        })
    
    order_details = {
        'id': order.id,
        'date': order.order_date.strftime('%Y-%m-%d %H:%M'),
        'status': order.status,
        'total': order.total_amount,
        'items': items
    }
    
    return jsonify(order_details)

# Authentication check
@user_bp.route('/api/check-auth')
def check_auth():
    return jsonify({
        'authenticated': current_user.is_authenticated
    })

# Page routes
@user_bp.route('/menu')
def menu_page():
    # Optional: Check if user has provided location (commented out to avoid redirect loop)
    # user_location = session.get('user_location')
    # if not user_location:
    #     return redirect(url_for('routes.location_page'))
    
    menu_items = MenuItem.query.filter_by(is_available=True).all()
    return render_template('menu.html', menu_items=menu_items)

@user_bp.route('/location', methods=['GET', 'POST'])
def location_page():
    if request.method == 'POST':
        try:
            # Log request details for debugging
            print(f"[DEBUG] Content-Type: {request.content_type}")
            print(f"[DEBUG] Request headers: {dict(request.headers)}")
            print(f"[DEBUG] Raw request data: {request.data}")
            
            data = request.get_json(force=True)
            print(f"[DEBUG] Location request data: {data}")
            print(f"[DEBUG] Data type: {type(data)}")
            
            if data and isinstance(data, dict):
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                
                print(f"[DEBUG] Latitude: {latitude}, Longitude: {longitude}")
                
                if latitude is not None and longitude is not None:
                    # Store location in session
                    session['user_location'] = {
                        'latitude': float(latitude),
                        'longitude': float(longitude),
                        'address': data.get('address', ''),
                        'skipped': data.get('skipped', False)
                    }
                    session.permanent = True
                    print(f"[DEBUG] Location saved to session: {session['user_location']}")
                    
                    # Different message based on whether location was skipped
                    if data.get('skipped', False):
                        print("[DEBUG] Location skipped successfully")
                        return jsonify({'success': True, 'message': 'Location skipped successfully'})
                    else:
                        print("[DEBUG] Location saved successfully")
                        return jsonify({'success': True, 'message': 'Location saved successfully'})
                else:
                    print(f"[DEBUG] Missing latitude or longitude. Data: {data}")
                    return jsonify({'success': False, 'message': 'Missing latitude or longitude'}), 400
            else:
                print(f"[DEBUG] Invalid data format. Data: {data}, Type: {type(data)}")
                return jsonify({'success': False, 'message': 'Invalid data format'}), 400
        except Exception as e:
            print(f"[ERROR] Error in location route: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
    
    return render_template('location.html')

@user_bp.route('/test-location')
def test_location_page():
    """Test page for debugging location functionality"""
    return render_template('test_location.html')

@user_bp.route('/checkout')
@login_required
def checkout_page():
    cart = session.get('cart', [])
    
    if not cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('menu_page'))
    
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    return render_template('checkout.html', cart=cart, total=total)

@user_bp.route('/receipt/<int:order_id>')
@login_required
def receipt_page(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('user.profile'))
    
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    
    items = []
    for item in order_items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        items.append({
            'name': menu_item.name,
            'quantity': item.quantity,
            'price': item.price,
            'total': item.price * item.quantity
        })
    
    return render_template('receipt.html', order=order, items=items)

# Helper function to generate verification code
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

# Helper function to send verification email
def send_verification_email(user):
    code = generate_verification_code()
    user.verification_code = code
    db.session.commit()
    
    msg = Message('Verify Your TastyBites Account', recipients=[user.email])
    msg.body = f'''Hello {user.name},

Thank you for signing up with TastyBites! To complete your registration, please verify your email address by entering the following 6-digit code:

{code}

If you did not sign up for TastyBites, please ignore this email.

Best regards,
The TastyBites Team
'''
    mail.send(msg)

# Main page routes
@user_bp.route('/')
def index():
    return render_template('index.html')

@user_bp.route('/about')
def about():
    return render_template('about.html')

@user_bp.route('/contact')
def contact():
    return render_template('contact.html')

# Authentication routes
@user_bp.route('/sign-up', methods=['GET', 'POST'])
def signup():
    error = None
    
    if request.method == 'POST':
        # Get form data
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        password = request.form.get('password')
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            error = f"The email address {email} is already registered. Please use a different email or login to your existing account."
            return render_template('signup.html', error=error)
        
        # Create new user
        new_user = User(
            name=fullname,
            email=email,
            phone=phone,
            address=address,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            role='user',
            is_verified=False
        )
        
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(new_user)
        
        # Store user_id in session for verification
        session['user_id_to_verify'] = new_user.id
        session.permanent = True
        
        # Redirect to verification page
        flash('Please check your email for a verification code.', 'info')
        return redirect(url_for('user.verify_email'))
    
    return render_template('signup.html', error=error)

@user_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    # Check if there's a user_id in session to verify
    user_id = session.get('user_id_to_verify')
    if not user_id:
        flash('Verification session expired. Please login again.', 'danger')
        return redirect(url_for('user.login'))
    
    # Get the user from database
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please register again.', 'danger')
        return redirect(url_for('user.signup'))
    
    if request.method == 'POST':
        user_code = request.form.get('code')
        
        # Validate the verification code
        if user.verification_code == user_code:
            # Mark user as verified
            user.is_verified = True
            user.verification_code = None  # Clear the code after successful verification
            db.session.commit()
            
            # Remove verification session
            session.pop('user_id_to_verify', None)
            
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')
    
    return render_template('verify_email.html')

@user_bp.route('/resend-code')
def resend_verification():
    # Check if there's a user_id in session to verify
    user_id = session.get('user_id_to_verify')
    if not user_id:
        flash('Verification session expired. Please login again.', 'danger')
        return redirect(url_for('user.login'))
    
    # Get the user from database
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please register again.', 'danger')
        return redirect(url_for('user.signup'))
    
    # Generate and send new verification code
    send_verification_email(user)
    
    flash('New verification code sent! Please check your email.', 'success')
    return redirect(url_for('user.verify_email'))

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if request.is_json:
            return jsonify({'redirect': url_for('user.index')})
        return redirect(url_for('user.index'))
        
    if request.method == 'POST':
        # Handle both form and JSON data
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            remember = data.get('remember', False)
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password, password):
            if request.is_json:
                return jsonify({'error': 'Invalid email or password'}), 401
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('user.login'))
        
        # Check if user is verified
        if not user.is_verified:
            # Store user_id in session for verification
            session['user_id_to_verify'] = user.id
            
            # Send verification email
            send_verification_email(user)
            
            if request.is_json:
                return jsonify({
                    'error': 'Please verify your email before logging in.',
                    'redirect': url_for('user.verify_email')
                }), 403
                
            flash('Please verify your email before logging in.', 'warning')
            return redirect(url_for('user.verify_email'))
        
        # If validation passes, log in the user
        from flask_login import login_user
        login_user(user, remember=remember)
        
        # Prepare response data
        response_data = {}
        
        # Redirect admin users to admin panel, regular users to index
        if user.role == 'admin':
            response_data['redirect'] = url_for('admin.dashboard')
        else:
            # Redirect to the page the user was trying to access or home
            next_page = request.args.get('next') or url_for('user.index')
            response_data['redirect'] = next_page
        
        if request.is_json:
            return jsonify(response_data)
        return redirect(response_data['redirect'])
    
    # If it's a GET request, just render the login page
    if request.is_json:
        return jsonify({'error': 'Method not allowed'}), 405
    return render_template('login.html')

@user_bp.route('/logout')
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    return redirect(url_for('user.index'))

@user_bp.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('profile.html', user=current_user, orders=orders)

# Password reset routes
@user_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('user.reset_with_token', token=token, _external=True)
            
            msg = Message('Password Reset Request', recipients=[user.email])
            msg.body = f'To reset your password, visit: {reset_url}'
            mail.send(msg)
            
            flash('Password reset instructions have been sent to your email.', 'info')
            return redirect(url_for('user.login'))
        
        flash('Email address not found.', 'danger')
        return redirect(url_for('user.reset_password'))
    
    return render_template('reset_password.html')

@user_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('user.reset_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('user.login'))
        
        flash('User not found.', 'danger')
        return redirect(url_for('user.reset_password'))
    
    return render_template('reset_password_confirm.html')

# Contact form submission
@user_bp.route('/submit-contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would typically save this to a database or send an email
        # For now, we'll just flash a message
        flash('Thank you for your message! We will get back to you soon.')
        return redirect(url_for('user.contact'))

# User authentication status API
@user_bp.route('/api/user/status')
def user_status():
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.name if current_user.is_authenticated else None
    })

# Place order route
@user_bp.route('/place-order', methods=['POST'])
def place_order():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please log in to place an order'}), 401
    
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': 'No items in order'}), 400
    
    # Create a new order
    new_order = Order(
        user_id=current_user.id,
        order_date=datetime.utcnow(),
        status='Pending',
        total_amount=data.get('total', 0)
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    # Add order items
    for item in items:
        order_item = OrderItem(
            order_id=new_order.id,
            menu_item_id=item['id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order placed successfully', 'order_id': new_order.id})
