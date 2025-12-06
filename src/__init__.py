from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from flask_migrate import Migrate
import os

# Load environment variables early so config is available for blueprint creation
load_dotenv()

from src.config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app() -> Flask:
    """
    Application factory for the Flask app.
    Loads environment variables, configures the database,
    and registers blueprints.
    """
    # Re-initialize config to ensure latest .env values are loaded
    from src.config import Config
    global config
    config = Config()
    
    # Validate configuration
    config.validate()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )

    # Load configuration from config module
    app.config["SECRET_KEY"] = config.SECRET_KEY
    db_uri = config.SQLALCHEMY_DATABASE_URI
    # Add connection pooling parameters for better performance
    if "?" not in db_uri:
        db_uri += "?charset=utf8mb4"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SQLALCHEMY_ECHO"] = config.SQLALCHEMY_ECHO
    # Database connection pooling for performance
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": 20,
        "connect_args": {
            "connect_timeout": 5,
            "read_timeout": 10,
            "write_timeout": 10,
        }
    }
    app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
    app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
    
    # Make config available to templates via context processor
    @app.context_processor
    def inject_config():
        return {
            "APP_CONFIG": {
                "API_BASE_URL": config.API_BASE_URL or config.API_PREFIX,
                "AUTH_API_PREFIX": config.AUTH_API_PREFIX,
                "STUDENT_API_PREFIX": config.STUDENT_API_PREFIX,
                "TUTOR_API_PREFIX": config.TUTOR_API_PREFIX,
            }
        }

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'login_page'  # This is the function name in __init__.py
    
    # Add response headers for caching and performance
    @app.after_request
    def add_performance_headers(response):
        """Add caching and performance headers to responses."""
        # Cache static files for 1 hour
        if request.endpoint == 'static' or request.path.startswith('/static/'):
            response.cache_control.max_age = 3600
            response.cache_control.public = True
        # Don't cache HTML pages (always fresh)
        elif response.content_type and 'text/html' in response.content_type:
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # User loader function for Flask-Login - optimized with caching
    @login_manager.user_loader
    def load_user(user_id):
        from src.auth.models import User
        # Use get() instead of query.get() for better performance
        # This uses SQLAlchemy's identity map cache
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Main routes - optimized for performance
    @app.route("/")
    def index():
        # Fast path: check authentication without DB query if possible
        if current_user.is_authenticated:
            if hasattr(current_user, 'user_type'):
                if current_user.user_type == 'student':
                    return redirect(url_for('student.dashboard'))
                elif current_user.user_type == 'tutor':
                    return redirect(url_for('tutor.dashboard'))
        # Use render_template for better caching and performance
        index_path = os.path.join(project_root, "templates", "index.html")
        if os.path.exists(index_path):
            return render_template("index.html")
        # Fallback to static file
        static_index = os.path.join(project_root, "static", "index.html")
        if os.path.exists(static_index):
            return send_file(static_index)
        # Last resort: return simple response
        return "Welcome to SenseLearn", 200

    @app.route("/login")
    @app.route("/auth")
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return render_template("register.html")

    @app.route("/forgot")
    def forgot_page():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return render_template("forgot.html")

    @app.route("/logout")
    def logout():
        from flask_login import logout_user
        from flask import flash
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login_page'))

    # Register blueprints
    from src.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register student blueprint
    from src.student import student_bp
    app.register_blueprint(student_bp)

    # Register tutor blueprint
    from src.tutor import tutor_bp
    app.register_blueprint(tutor_bp)

        # Create tables if they do not exist
        with app.app_context():
            from src.auth.models import User, PasswordResetCode
            db.create_all()

    return app