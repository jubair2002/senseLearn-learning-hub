from datetime import datetime, timedelta

from src import db


class User(db.Model):
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
    # -----------------------------------

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