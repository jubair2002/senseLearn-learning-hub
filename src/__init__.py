from flask import Flask, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()


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

    db.init_app(app)

    # Serve the main landing page and auth pages from HTML templates
    @app.route("/")
    def index():
        # index.html still lives at project root, served as a static file
        return send_file(os.path.join(project_root, "index.html"))

    @app.route("/login")
    @app.route("/auth")  # backward compatible
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/forgot")
    def forgot_page():
        return render_template("forgot.html")

    # Register blueprints
    from src.auth import auth_bp  # type: ignore

    app.register_blueprint(auth_bp)

    # Create tables if they do not exist
    with app.app_context():
        from src.auth.models import User, PasswordResetCode  # noqa: F401

        db.create_all()

    return app


