from datetime import datetime, timedelta
from flask_login import UserMixin

from src import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- User Type (Student/Tutor) ---
    user_type = db.Column(db.String(20), nullable=False, default="student")  # 'student' or 'tutor'
    
    # --- Common Fields for Both ---
    full_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # --- Student Specific Fields ---
    disability_type = db.Column(db.String(50), nullable=True)  # Only for students
    
    # --- Tutor Specific Fields ---
    qualifications = db.Column(db.Text, nullable=True)  # Tutor's qualifications
    experience_years = db.Column(db.Integer, nullable=True)  # Years of experience
    subjects = db.Column(db.String(255), nullable=True)  # Subjects tutor can teach
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # Hourly rate
    bio = db.Column(db.Text, nullable=True)  # Short bio/description
    is_verified = db.Column(db.Boolean, default=False)  # Tutor verification status
    
    # --- Email Verification ---
    email_verified = db.Column(db.Boolean, default=False)  # Email verification status

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} ({self.user_type})>"

    def is_student(self) -> bool:
        return self.user_type == "student"
    
    def is_tutor(self) -> bool:
        return self.user_type == "tutor"


class PasswordResetCode(db.Model):
    __tablename__ = "password_reset_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    code = db.Column(db.String(20), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="reset_codes")

    @classmethod
    def create_for_user(cls, user: User, code: str, minutes_valid: int = 15) -> "PasswordResetCode":
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(user=user, code=code, expires_at=expires)


class EmailVerificationOTP(db.Model):
    __tablename__ = "email_verification_otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)  # Nullable for pending registrations, indexed for faster queries
    email = db.Column(db.String(255), nullable=True, index=True)  # For pending registrations before user exists
    otp = db.Column(db.String(20), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)  # Indexed for expiration cleanup queries
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Indexed for ordering queries
    purpose = db.Column(db.String(50), nullable=False, default="verification", index=True)  # Indexed for filtering by purpose

    user = db.relationship("User", backref="verification_otps")
    
    # Add composite index for common query patterns (email + purpose, user_id + purpose)
    __table_args__ = (
        db.Index('ix_email_purpose', 'email', 'purpose'),
        db.Index('ix_user_purpose', 'user_id', 'purpose'),
        db.Index('ix_email_otp', 'email', 'otp', 'purpose'),
    )

    @classmethod
    def create_for_user(cls, user: User, otp: str, minutes_valid: int = 10, purpose: str = "verification") -> "EmailVerificationOTP":
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(user=user, otp=otp, expires_at=expires, purpose=purpose)
    
    @classmethod
    def create_for_email(cls, email: str, otp: str, minutes_valid: int = 10, purpose: str = "verification") -> "EmailVerificationOTP":
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(email=email, otp=otp, expires_at=expires, purpose=purpose)


class PendingRegistration(db.Model):
    """Temporary storage for registration data before email verification."""
    __tablename__ = "pending_registrations"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # Registration data stored as JSON
    registration_data = db.Column(db.Text, nullable=False)  # JSON string with all registration fields
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def create(cls, email: str, registration_data: dict, minutes_valid: int = 30) -> "PendingRegistration":
        import json
        expires = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(
            email=email,
            registration_data=json.dumps(registration_data),
            expires_at=expires
        )
    
    def get_registration_data(self) -> dict:
        import json
        return json.loads(self.registration_data)