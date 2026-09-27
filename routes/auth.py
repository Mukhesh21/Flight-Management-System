from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from models import db, User, PassengerProfile, StaffProfile, Notification

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                flash('Access denied. You do not have permission to view this page.', 'danger')
                if user_role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user_role == 'staff':
                    return redirect(url_for('staff.desk'))
                return redirect(url_for('passenger.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def staff_required(f):
    return role_required('admin', 'staff')(f)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('passenger.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'passenger').lower()

        # Simple validations
        if not username or not email or not full_name or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please login.', 'danger')
            return render_template('auth/register.html')

        # Limit self-registration to passenger or demo staff
        allowed_reg_roles = ['passenger', 'staff', 'admin']
        if role not in allowed_reg_roles:
            role = 'passenger'

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        if role == 'passenger':
            profile = PassengerProfile(
                user_id=new_user.id,
                passport_number=request.form.get('passport_number', '').strip(),
                nationality=request.form.get('nationality', 'Indian'),
                frequent_flyer_no=f"FF{new_user.id:06d}"
            )
            db.session.add(profile)
        elif role == 'staff':
            staff_prof = StaffProfile(
                user_id=new_user.id,
                employee_id=f"EMP-{new_user.id:04d}",
                department=request.form.get('department', 'Ground Operations'),
                airport_code=request.form.get('airport_code', 'DEL')
            )
            db.session.add(staff_prof)

        # Welcome notification
        welcome_notif = Notification(
            user_id=new_user.id,
            title='Welcome to SkyWings Airlines!',
            message=f'Welcome {full_name}! Your account has been registered successfully as {role.capitalize()}.',
            notification_type='system',
            link_url=url_for('passenger.dashboard') if role == 'passenger' else None
        )
        db.session.add(welcome_notif)
        db.session.commit()

        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'staff':
            return redirect(url_for('staff.desk'))
        return redirect(url_for('passenger.dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not login_input or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter((User.username == login_input) | (User.email == login_input.lower())).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html')

            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            session['full_name'] = user.full_name

            flash(f'Welcome back, {user.full_name}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('staff.desk'))
            else:
                return redirect(url_for('passenger.dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get_or_404(session['user_id'])
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', user.full_name).strip()
        user.phone = request.form.get('phone', user.phone).strip()

        if user.is_passenger:
            profile = user.passenger_profile
            if not profile:
                profile = PassengerProfile(user_id=user.id)
                db.session.add(profile)
            profile.passport_number = request.form.get('passport_number', '').strip()
            profile.nationality = request.form.get('nationality', 'Indian').strip()
            profile.emergency_contact = request.form.get('emergency_contact', '').strip()
            profile.address = request.form.get('address', '').strip()

        new_password = request.form.get('new_password', '')
        if new_password:
            current_password = request.form.get('current_password', '')
            if not user.check_password(current_password):
                flash('Incorrect current password. Password was not updated.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            else:
                user.set_password(new_password)
                flash('Password updated successfully.', 'success')

        db.session.commit()
        session['full_name'] = user.full_name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=user)
