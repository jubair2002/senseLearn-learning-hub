from datetime import datetime, timedelta

from src import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- New Fields for Registration ---
    full_name = db.Column(db.String(255), nullable=False) # New: Required
    username = db.Column(db.String(50), unique=True, nullable=True) # New: Optional, unique
    phone_number = db.Column(db.String(20), nullable=True) # New: Optional
    disability_type = db.Column(db.String(50), nullable=False) # New: Required (Dropdown)
    # -----------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"


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