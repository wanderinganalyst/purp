
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User
from address_verification import verify_address, format_address
from rep_lookup import RepresentativeLookup
from utils.data_fetcher import get_data_fetcher
from functools import wraps
from utils.validators import (
    validate_username, 
    validate_password, 
    validate_address, 
    validate_apt_unit,
    sanitize_input
)

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)

    return decorated


def role_required(role_name):
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session:
                flash('Please log in to access this page.')
                return redirect(url_for('auth.login', next=request.path))
            if session.get('role') != role_name:
                flash('You do not have permission to access this page.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)

        return decorated

    return decorator


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get and sanitize form data
        username = sanitize_input(request.form.get('username', ''), 150)
        password = request.form.get('password', '')
        verify_password = request.form.get('verify_password', '')
        street_address = sanitize_input(request.form.get('street_address', ''), 255)
        apt_unit = sanitize_input(request.form.get('apt_unit', ''), 50) or None
        city = sanitize_input(request.form.get('city', ''), 100)
        state = sanitize_input(request.form.get('state', ''), 2).upper()
        zipcode = sanitize_input(request.form.get('zipcode', ''), 10)

        # Validate username
        valid, error = validate_username(username)
        if not valid:
            flash(error)
            return redirect(url_for('auth.register'))

        # Validate password
        valid, error = validate_password(password)
        if not valid:
            flash(error)
            return redirect(url_for('auth.register'))
        
        # Verify passwords match
        if password != verify_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.register'))

        # Validate address
        valid, error = validate_address(street_address, city, state, zipcode)
        if not valid:
            flash(error)
            return redirect(url_for('auth.register'))
        
        # Validate apt_unit if provided
        if apt_unit:
            valid, error = validate_apt_unit(apt_unit)
            if not valid:
                flash(error)
                return redirect(url_for('auth.register'))

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))

        # Verify address
        is_valid, standardized = verify_address(
            street_address, city, state, zipcode, apt_unit
        )

        if not is_valid:
            flash('Invalid address. Please check and try again.')
            return redirect(url_for('auth.register'))

        # Create new user with verified address
        new_user = User(
            username=username,
            street_address=standardized['street_address'],
            apt_unit=standardized['apt_unit'],
            city=standardized['city'],
            state=standardized['state'],
            zipcode=standardized['zipcode'],
            address_verified=True
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth_bp.route('/profile')
@login_required
def profile():
    # Get the current user
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.login'))
    
    # Look up representatives for the user's address
    rep_info = None
    if user.address_verified:
        # Use data fetcher - handles production vs development automatically
        data_fetcher = get_data_fetcher()
        address_data = {
            'street': user.street_address,
            'city': user.city,
            'state': 'MO',
            'zip': user.zipcode
        }
        rep_info = data_fetcher.fetch_representatives(address_data)
    
    return render_template('auth/profile.html', user=user, rep_info=rep_info)

@auth_bp.route('/edit-address', methods=['GET', 'POST'])
@login_required
def edit_address():
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        street_address = request.form.get('street_address', '').strip()
        apt_unit = request.form.get('apt_unit', '').strip() or None
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zipcode = request.form.get('zipcode', '').strip()
        
        if not all([street_address, city, state, zipcode]):
            flash('All fields except apartment/unit are required.')
            return redirect(url_for('auth.edit_address'))
        
        # Verify new address
        is_valid, standardized = verify_address(
            street_address, city, state, zipcode, apt_unit
        )
        
        if not is_valid:
            flash('Invalid address. Please check and try again.')
            return redirect(url_for('auth.edit_address'))
        
        # Update user's address
        try:
            user.street_address = standardized['street_address']
            user.apt_unit = standardized['apt_unit']
            user.city = standardized['city']
            user.state = standardized['state']
            user.zipcode = standardized['zipcode']
            user.address_verified = True
            
            db.session.commit()
            flash('Address updated successfully.')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating address. Please try again.')
            return redirect(url_for('auth.edit_address'))
    
    return render_template('auth/edit_address.html', user=user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found.')
            return redirect(url_for('auth.login'))
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not user.check_password(current_password):
            flash('Current password is incorrect.')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.')
            return redirect(url_for('auth.change_password'))
        
        user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully.')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Sanitize inputs
        username = sanitize_input(request.form.get('username', ''), 150)
        password = request.form.get('password', '')
        
        # Basic validation
        if not username:
            flash('Username is required.')
            return render_template('login.html')
        
        if not password:
            flash('Password is required.')
            return render_template('login.html')
        
        # Validate username format
        valid, error = validate_username(username)
        if not valid:
            flash('Invalid username or password.')
            return render_template('login.html')
        
        # Check credentials
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Logged in successfully.')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        
        flash('Invalid username or password.')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get and sanitize inputs
        username = sanitize_input(request.form.get('username', ''), 150)
        password = request.form.get('password', '')
        verify_password = request.form.get('verify_password', '')
        street_address = sanitize_input(request.form.get('street_address', ''), 255)
        apt_unit = sanitize_input(request.form.get('apt_unit', ''), 50)
        city = sanitize_input(request.form.get('city', ''), 100)
        state = sanitize_input(request.form.get('state', ''), 2).upper()
        zipcode = sanitize_input(request.form.get('zipcode', ''), 10)
        role = request.form.get('role', 'regular')
        
        # Validate username
        valid, error = validate_username(username)
        if not valid:
            flash(error)
            return render_template('signup.html')
        
        # Validate password
        valid, error = validate_password(password)
        if not valid:
            flash(error)
            return render_template('signup.html')
        
        # Verify passwords match
        if password != verify_password:
            flash('Passwords do not match.')
            return render_template('signup.html')
        
        # Validate address
        valid, error = validate_address(street_address, city, state, zipcode)
        if not valid:
            flash(error)
            return render_template('signup.html')
        
        # Validate apt_unit if provided
        valid, error = validate_apt_unit(apt_unit)
        if not valid:
            flash(error)
            return render_template('signup.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.')
            return render_template('signup.html')
        
        # Validate role
        if role not in ['regular', 'power']:
            role = 'regular'
        
        # Create new user
        user = User(
            username=username,
            role=role,
            street_address=street_address,
            apt_unit=apt_unit if apt_unit else None,
            city=city,
            state=state,
            zipcode=zipcode,
            address_verified=False
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Lookup representatives for the user's address
            try:
                # Use data fetcher - handles production vs development automatically
                data_fetcher = get_data_fetcher()
                address_data = {
                    'street': street_address + (f" {apt_unit}" if apt_unit else ""),
                    'city': city,
                    'state': 'MO',
                    'zip': zipcode
                }
                rep_info = data_fetcher.fetch_representatives(address_data)
                
                if rep_info:
                    user.update_representatives(rep_info)
                    db.session.commit()
            except Exception as e:
                # Don't fail signup if rep lookup fails
                print(f"Error looking up representatives: {e}")
            
            flash('Account created successfully! Please log in.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.')
            return render_template('signup.html')

    return render_template('signup.html')
