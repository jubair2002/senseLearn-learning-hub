"""
Configuration module for the application.
All configuration values are read from environment variables.
No defaults - all values must be set in .env file.
"""
import os
import secrets
import warnings


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Flask Configuration
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.FLASK_ENV: str = os.getenv("FLASK_ENV", "")
        self.FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "").lower() == "true"
        
        # Generate a development SECRET_KEY if not set and in development mode
        if not self.SECRET_KEY and self.FLASK_ENV != "production":
            self.SECRET_KEY = secrets.token_urlsafe(32)
            warnings.warn(
                "SECRET_KEY not set. Generated a temporary key for development. "
                "Set SECRET_KEY in your .env file for production!",
                UserWarning
            )
        
        # Database Configuration
        self.DB_USER: str = os.getenv("DB_USER", "")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        self.DB_HOST: str = os.getenv("DB_HOST", "")
        self.DB_PORT: str = os.getenv("DB_PORT", "")
        self.DB_NAME: str = os.getenv("DB_NAME", "")
        
        # API Configuration
        self.API_PREFIX: str = os.getenv("API_PREFIX", "")
        self.AUTH_API_PREFIX: str = os.getenv("AUTH_API_PREFIX", "")
        self.STUDENT_API_PREFIX: str = os.getenv("STUDENT_API_PREFIX", "")
        self.TUTOR_API_PREFIX: str = os.getenv("TUTOR_API_PREFIX", "")
        
        # Application URLs (for frontend)
        self.APP_BASE_URL: str = os.getenv("APP_BASE_URL", "")
        self.API_BASE_URL: str = os.getenv("API_BASE_URL", "")
        
        # Password Reset Configuration
        reset_code_length = os.getenv("RESET_CODE_LENGTH", "")
        self.RESET_CODE_LENGTH: int = int(reset_code_length) if reset_code_length else 0
        reset_validity = os.getenv("RESET_CODE_VALIDITY_MINUTES", "")
        self.RESET_CODE_VALIDITY_MINUTES: int = int(reset_validity) if reset_validity else 0
        
        # Password Validation
        min_pass_len = os.getenv("MIN_PASSWORD_LENGTH", "")
        self.MIN_PASSWORD_LENGTH: int = int(min_pass_len) if min_pass_len else 0
        
        # User Type Validation
        valid_user_types = os.getenv("VALID_USER_TYPES", "")
        self.VALID_USER_TYPES: list[str] = [t.strip() for t in valid_user_types.split(",")] if valid_user_types else []
        self.DEFAULT_USER_TYPE: str = os.getenv("DEFAULT_USER_TYPE", "")
        
        valid_disability_types = os.getenv("VALID_DISABILITY_TYPES", "")
        self.VALID_DISABILITY_TYPES: list[str] = [t.strip() for t in valid_disability_types.split(",")] if valid_disability_types else []
        
        # Blueprint URL Prefixes
        self.STUDENT_URL_PREFIX: str = os.getenv("STUDENT_URL_PREFIX", "")
        self.TUTOR_URL_PREFIX: str = os.getenv("TUTOR_URL_PREFIX", "")
        
        # Success Messages
        self.MSG_STUDENT_REGISTER_SUCCESS: str = os.getenv("MSG_STUDENT_REGISTER_SUCCESS", "")
        self.MSG_TUTOR_REGISTER_SUCCESS: str = os.getenv("MSG_TUTOR_REGISTER_SUCCESS", "")
        self.MSG_LOGIN_SUCCESS: str = os.getenv("MSG_LOGIN_SUCCESS", "")
        self.MSG_LOGOUT_SUCCESS: str = os.getenv("MSG_LOGOUT_SUCCESS", "")
        self.MSG_PASSWORD_RESET_SUCCESS: str = os.getenv("MSG_PASSWORD_RESET_SUCCESS", "")
        
        # Session Configuration
        session_secure = os.getenv("SESSION_COOKIE_SECURE", "")
        self.SESSION_COOKIE_SECURE: bool = session_secure.lower() == "true" if session_secure else False
        session_httponly = os.getenv("SESSION_COOKIE_HTTPONLY", "")
        self.SESSION_COOKIE_HTTPONLY: bool = session_httponly.lower() == "true" if session_httponly else False
        self.SESSION_COOKIE_SAMESITE: str = os.getenv("SESSION_COOKIE_SAMESITE", "")
        
        # SQLAlchemy Configuration
        self.SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
        sqlalchemy_echo = os.getenv("SQLALCHEMY_ECHO", "")
        self.SQLALCHEMY_ECHO: bool = sqlalchemy_echo.lower() == "true" if sqlalchemy_echo else False
        
        # Email Configuration (SMTP)
        self.SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
        self.SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
        self.SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
        self.SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # OTP Configuration
        otp_length = os.getenv("OTP_LENGTH", "")
        self.OTP_LENGTH: int = int(otp_length) if otp_length else 6
        otp_validity = os.getenv("OTP_VALIDITY_MINUTES", "")
        self.OTP_VALIDITY_MINUTES: int = int(otp_validity) if otp_validity else 10
        
        # File Upload Configuration
        self.UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "D:/uploads")  # Default to D:/uploads for local testing
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # Default 10MB in bytes
        # Convert extensions to lowercase for case-insensitive matching
        allowed_exts_str = os.getenv("ALLOWED_EXTENSIONS", "pdf,doc,docx,jpg,jpeg,png,ppt,pptx,gif,txt")
        self.ALLOWED_EXTENSIONS: set = set(ext.strip().lower() for ext in allowed_exts_str.split(","))
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Construct database URI from environment variables."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def validate(self) -> None:
        """
        Validate required configuration values.
        Only enforces SECRET_KEY in production environment.
        """
        if not self.SECRET_KEY:
            if self.FLASK_ENV == "production":
                raise ValueError(
                    "SECRET_KEY environment variable is required in production. "
                    "Set it in your .env file or environment variables."
                )
            # For non-production, a warning was already issued in __init__


# Global config instance - will be re-initialized after load_dotenv()
config = Config()
