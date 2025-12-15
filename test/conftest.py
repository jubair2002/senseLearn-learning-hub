"""
Pytest configuration and fixtures for testing.
Simplified version without database dependencies.
"""
import pytest
import os
from unittest.mock import Mock

# Mock db.create_all BEFORE any imports that might use it
# This prevents database initialization during app creation
import sys

# Create a mock db module that won't try to connect
class MockDB:
    def create_all(self):
        pass
    def drop_all(self):
        pass
    def init_app(self, app):
        pass
    @property
    def session(self):
        return Mock()
    def __getattr__(self, name):
        return Mock()

# Try to patch db before create_app imports it
try:
    from src import db
    db.create_all = Mock(return_value=None)
except:
    pass

from src import create_app


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    # Set test environment variables BEFORE creating app
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'sfndsfojoriwew09rjfjndsknfkj'
    os.environ['UPLOAD_DIR'] = '/tmp/test_uploads'
    os.environ['API_PREFIX'] = '/api'
    os.environ['AUTH_API_PREFIX'] = '/auth/api'
    os.environ['STUDENT_API_PREFIX'] = '/student/api'
    os.environ['TUTOR_API_PREFIX'] = '/tutor/api'
    os.environ['VALID_USER_TYPES'] = 'student,tutor,admin'
    os.environ['DEFAULT_USER_TYPE'] = 'student'
    os.environ['VALID_DISABILITY_TYPES'] = 'Deaf,Mute,Blind,Physical,All'
    os.environ['MIN_PASSWORD_LENGTH'] = '8'
    os.environ['OTP_LENGTH'] = '6'
    os.environ['OTP_VALIDITY_MINUTES'] = '10'
    os.environ['MAX_FILE_SIZE'] = '10485760'
    os.environ['ALLOWED_EXTENSIONS'] = 'pdf,doc,docx,jpg,jpeg,png,ppt,pptx,gif,txt,mp4,webm,avi,mov,mkv'
    
    # Set empty DB config - this prevents MySQL connection attempt
    os.environ['DB_USER'] = ''
    os.environ['DB_PASSWORD'] = ''
    os.environ['DB_HOST'] = ''
    os.environ['DB_PORT'] = ''
    os.environ['DB_NAME'] = ''
    
    # Mock both db.create_all and db.init_app to prevent database connection
    from src import db
    original_create_all = db.create_all
    original_init_app = db.init_app
    
    db.create_all = Mock(return_value=None)
    db.init_app = Mock(return_value=None)  # Prevent database initialization
    
    # Create app - database operations are mocked
    try:
        app = create_app()
    except Exception as e:
        # If still fails, create minimal app
        error_msg = str(e).lower()
        if any(kw in error_msg for kw in ['key was too long', 'cryptography', '1071', 'operationalerror', 'pymysql']):
            from flask import Flask
            app = Flask(__name__)
            app.config['TESTING'] = True
            app.config['SECRET_KEY'] = 'test-secret-key'
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            app.config['WTF_CSRF_ENABLED'] = False
            
            # Register blueprints
            from src.auth import auth_bp
            from src.student import student_bp
            from src.tutor import tutor_bp
            from src.admin import admin_bp
            app.register_blueprint(auth_bp)
            app.register_blueprint(student_bp)
            app.register_blueprint(tutor_bp)
            app.register_blueprint(admin_bp)
        else:
            raise
    finally:
        # Restore originals (though not needed for tests)
        db.create_all = original_create_all
        db.init_app = original_init_app
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    if 'SQLALCHEMY_DATABASE_URI' in app.config:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    yield app


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = Mock()
    user.id = 1
    user.email = 'test@test.com'
    user.full_name = 'Test User'
    user.user_type = 'student'
    user.email_verified = True
    user.is_verified = True
    user.is_authenticated = True
    return user
