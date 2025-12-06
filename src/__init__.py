from flask import Flask, render_template, send_file, redirect, url_for
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
    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SQLALCHEMY_ECHO"] = config.SQLALCHEMY_ECHO
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

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from src.auth.models import User
        return User.query.get(int(user_id))

    # Main routes
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if hasattr(current_user, 'user_type'):
                if current_user.user_type == 'student':
                    return redirect(url_for('student.dashboard'))
                elif current_user.user_type == 'tutor':
                    return redirect(url_for('tutor.dashboard'))
        # Serve index.html from static folder
        return send_file(os.path.join(project_root, "static", "index.html"))

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
        return redirect(url_for('index'))

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