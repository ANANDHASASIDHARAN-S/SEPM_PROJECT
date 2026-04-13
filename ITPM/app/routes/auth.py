from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.models import db, User, Employee, Role
from app.forms import LoginForm, RegistrationForm
from app.utils import log_audit
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=Role[form.role.data.upper().replace(' ', '_')] if hasattr(Role, form.role.data.upper().replace(' ', '_')) else Role.EMPLOYEE
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.flush()  # Flush to get the user ID
            
            # Create employee record if registering as employee
            role_obj = Role(form.role.data)
            if role_obj in (Role.EMPLOYEE, Role.PROJECT_MANAGER, Role.HR_MANAGER):
                employee = Employee(
                    user_id=user.id,
                    first_name=form.username.data,
                    last_name='User',
                    email=form.email.data,
                    hire_date=datetime.utcnow().date()
                )
                db.session.add(employee)
            
            db.session.commit()
            
            log_audit('CREATE', 'User', user.id, {'username': user.username, 'role': user.role.value})
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form, title='Register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login user"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account is disabled.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=True)
            log_audit('LOGIN', 'User', user.id)
            
            next_page = request.args.get('next')
            if not next_page or url_has_allowed_host_and_scheme(next_page):
                next_page = url_for('main.dashboard')
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html', form=form, title='Login')

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    if current_user.is_authenticated:
        log_audit('LOGOUT', 'User', current_user.id)
        logout_user()
        flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

def url_has_allowed_host_and_scheme(url, allowed_hosts=None, require_https=False):
    """Check if URL is safe to redirect to"""
    from urllib.parse import urlparse
    if allowed_hosts is None:
        allowed_hosts = set()
    
    parsed = urlparse(url)
    if url.startswith(('//', '\\/')):
        return False
    if parsed.netloc and parsed.netloc not in allowed_hosts:
        return False
    return True
