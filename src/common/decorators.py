from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to require student role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.user_type != 'student':
            flash('This page is only accessible to students.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def tutor_required(f):
    """Decorator to require tutor role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.user_type != 'tutor':
            flash('This page is only accessible to tutors.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def tutor_verified_required(f):
    """Decorator to require tutor verification for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.user_type != 'tutor':
            flash('This page is only accessible to tutors.', 'error')
            return redirect(url_for('main.index'))
        if not current_user.is_verified:
            flash('Your tutor account needs to be verified to access this feature.', 'warning')
            return redirect(url_for('tutor.verification'))
        return f(*args, **kwargs)
    return decorated_function