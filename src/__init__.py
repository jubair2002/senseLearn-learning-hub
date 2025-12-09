from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_compress import Compress
import os

# Load environment variables early so config is available for blueprint creation
load_dotenv()

from src.config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
compress = Compress()

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
        "pool_reset_on_return": "commit",  # Reset connections on return for better performance
        "connect_args": {
            "connect_timeout": 5,
            "read_timeout": 10,
            "write_timeout": 10,
            "charset": "utf8mb4",
            "autocommit": False,
        }
    }
    
    # Response compression settings
    app.config["COMPRESS_MIMETYPES"] = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript'
    ]
    app.config["COMPRESS_LEVEL"] = 6  # Balance between compression and CPU
    app.config["COMPRESS_MIN_SIZE"] = 500  # Only compress responses > 500 bytes
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
    compress.init_app(app)  # Enable response compression
    
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
                elif current_user.user_type == 'admin':
                    return redirect(url_for('admin.dashboard'))
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
    
    @app.route("/uploads/<path:file_path>")
    @login_required
    def serve_upload(file_path):
        """Serve uploaded files securely."""
        from src.config import config as app_config
        import os
        
        try:
            # Security: Ensure file is within uploads directory
            # Normalize the file path to prevent directory traversal
            normalized_path = file_path.replace("\\", "/")
            full_path = os.path.join(app_config.UPLOAD_DIR, normalized_path)
            
            # Normalize path to prevent directory traversal
            full_path = os.path.normpath(full_path)
            upload_dir = os.path.normpath(app_config.UPLOAD_DIR)
            
            # Security check: ensure file is within uploads directory
            if not full_path.startswith(upload_dir):
                current_app.logger.warning(f"Directory traversal attempt: {file_path}")
                return "Forbidden", 403
            
            if not os.path.exists(full_path):
                current_app.logger.warning(f"File not found: {full_path}")
                return "File not found", 404
            
            if not os.path.isfile(full_path):
                current_app.logger.warning(f"Path is not a file: {full_path}")
                return "Not a file", 400
            
            # Check if user has permission to view this file
            # Tutors can view their own files, admins can view all tutor files
            if 'tutors' in normalized_path:
                try:
                    # Extract tutor ID from path (format: tutors/{tutor_id}/...)
                    parts = normalized_path.split('tutors/')
                    if len(parts) > 1:
                        tutor_id_str = parts[1].split('/')[0]
                        tutor_id = int(tutor_id_str)
                        
                        # Allow if current user is the tutor or an admin
                        if current_user.is_authenticated:
                            is_tutor_owner = current_user.id == tutor_id
                            is_admin = hasattr(current_user, 'user_type') and current_user.user_type == 'admin'
                            
                            if is_tutor_owner or is_admin:
                                # Determine MIME type for proper browser handling
                                from mimetypes import guess_type
                                mime_type, _ = guess_type(full_path)
                                if not mime_type:
                                    mime_type = 'application/octet-stream'
                                
                                # Send file with proper headers for inline display
                                response = send_file(
                                    full_path,
                                    mimetype=mime_type,
                                    as_attachment=False,  # Display inline instead of downloading
                                    conditional=True  # Enable conditional requests (304 Not Modified)
                                )
                                # Add headers for proper PDF display in iframe
                                response.headers['Content-Disposition'] = f'inline; filename="{os.path.basename(full_path)}"'
                                response.headers['X-Content-Type-Options'] = 'nosniff'
                                # Optimized cache headers - longer cache for static files
                                response.cache_control.max_age = 86400  # 24 hours
                                response.cache_control.public = True
                                # Add ETag for better caching
                                import hashlib
                                file_stat = os.stat(full_path)
                                etag = hashlib.md5(f"{full_path}{file_stat.st_mtime}{file_stat.st_size}".encode()).hexdigest()
                                response.headers['ETag'] = f'"{etag}"'
                                return response
                            else:
                                current_app.logger.warning(f"Access denied: User {current_user.id} tried to access tutor {tutor_id} file")
                                return "Forbidden", 403
                        else:
                            return "Unauthorized", 401
                except (ValueError, IndexError) as e:
                    current_app.logger.error(f"Error parsing tutor ID from path {file_path}: {str(e)}")
                    return "Invalid file path", 400
            
            # If path doesn't match expected pattern, deny access
            current_app.logger.warning(f"Access denied for file path: {file_path}")
            return "Forbidden", 403
            
        except Exception as e:
            current_app.logger.exception(f"Error serving file {file_path}: {str(e)}")
            return "Internal server error", 500

    # Register blueprints
    from src.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register student blueprint
    from src.student import student_bp
    app.register_blueprint(student_bp)

    # Register tutor blueprint
    from src.tutor import tutor_bp
    app.register_blueprint(tutor_bp)

    # Register admin blueprint
    from src.admin import admin_bp
    app.register_blueprint(admin_bp)

    # Create tables if they do not exist
    with app.app_context():
        from src.auth.models import User, PasswordResetCode
        db.create_all()

    return app