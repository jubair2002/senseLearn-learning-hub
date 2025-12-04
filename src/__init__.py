from flask import Flask, render_template, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app() -> Flask:
    """
    Application factory for the Flask app.
    Loads environment variables, configures the database,
    and registers blueprints.
    """
    load_dotenv()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )

    # Basic configuration from environment
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY environment variable is required. "
            "Set it in your .env file, e.g. SECRET_KEY=your-random-secret"
        )
    app.config["SECRET_KEY"] = secret_key

    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "senselearn_db")

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
                    return redirect('/student/dashboard')
                else:
                    return redirect('/tutor/dashboard')
        return send_file(os.path.join(project_root, "index.html"))

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
    try:
        from src.student import student_bp
        app.register_blueprint(student_bp)
    except ImportError:
        # Student module not created yet, will be created in next steps
        pass

    # Register tutor blueprint
    try:
        from src.tutor import tutor_bp
        app.register_blueprint(tutor_bp)
    except ImportError:
        # Tutor module not created yet, will be created in next steps
        pass

    # Create tables if they do not exist
    with app.app_context():
        from src.auth.models import User, PasswordResetCode
        db.create_all()

    return app