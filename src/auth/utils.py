import random
import re
import string
from typing import Optional

from passlib.hash import bcrypt
from src.config import config


EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def _truncate_password(plain_password: str) -> str:
    """Helper to consistently truncate password to its first 72 UTF-8 bytes."""
    # Encode to bytes, take the first 72 bytes, and decode back to a string,
    # ignoring any incomplete multi-byte characters at the truncation point.
    password_bytes = plain_password.encode('utf-8')[:72]
    return password_bytes.decode('utf-8', errors='ignore')


def hash_password(plain_password: str) -> str:
    """
    Hash password using bcrypt. It is truncated to the first 72 bytes
    of its UTF-8 encoding before hashing.
    """
    truncated = _truncate_password(plain_password)
    return bcrypt.hash(truncated)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against a hash, using the same truncation as hash_password."""
    truncated = _truncate_password(plain_password)
    return bcrypt.verify(truncated, password_hash)


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_REGEX.match(email))


def validate_password(password: str) -> tuple[bool, str | None]:
    """
    Basic server-side password validation.
    Returns (is_valid, error_message).
    """
    min_length = config.MIN_PASSWORD_LENGTH
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    # The 72-byte truncation is handled consistently in hash_password() and verify_password().

    return True, None


def generate_reset_code(length: Optional[int] = None) -> str:
    """
    Generate a numeric reset code.
    Default length is read from configuration.
    """
    if length is None:
        length = config.RESET_CODE_LENGTH
    return "".join(random.choices(string.digits, k=length))


def generate_otp(length: Optional[int] = None) -> str:
    """
    Generate a numeric OTP code.
    Default length is read from configuration.
    """
    if length is None:
        length = config.OTP_LENGTH
    return "".join(random.choices(string.digits, k=length))