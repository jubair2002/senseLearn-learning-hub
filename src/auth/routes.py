from datetime import datetime

from flask import current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from src import db
from src.auth import auth_bp
from src.auth.models import PasswordResetCode, User
from src.auth.utils import (
    generate_reset_code,
    hash_password,
    is_valid_email,
    validate_password,
    verify_password,
)


@auth_bp.route("/", methods=["GET"])
def auth_root():
    """Simple health/info endpoint for /api/auth."""
    return jsonify(
        {
            "status": "ok",
            "message": "Auth API is running",
            "endpoints": ["/register", "/login", "/forgot", "/reset"],
        }
    ), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        if not is_valid_email(email):
            return jsonify({"message": "Please provide a valid email address"}), 400

        ok, error = validate_password(password)
        if not ok:
            return jsonify({"message": error}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"message": "User with this email already exists"}), 409

        user = User(email=email, password_hash=hash_password(password))

        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as exc:  # DB or connection error
        db.session.rollback()
        current_app.logger.exception("Error while registering user")
        return (
            jsonify(
                {
                    "message": "Internal server error while creating user. "
                    "Please contact support or try again later."
                }
            ),
            500,
        )
    except Exception as exc:  # any other unexpected error
        current_app.logger.exception("Unhandled error while registering user")
        return (
            jsonify(
                {
                    "message": "Unexpected server error during registration.",
                    "detail": str(exc),
                }
            ),
            500,
        )

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"message": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "user": {"email": user.email}}), 200


@auth_bp.route("/forgot", methods=["POST"])
def forgot_password():
    """
    Generate and store a reset code for the user.
    In a real system, you'd email or SMS this code.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    PasswordResetCode.query.filter_by(user_id=user.id).delete()

    code = generate_reset_code()
    reset_obj = PasswordResetCode.create_for_user(user, code)
    db.session.add(reset_obj)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Reset code generated",
                "code": code,
                "expires_at": reset_obj.expires_at.isoformat() + "Z",
            }
        ),
        200,
    )


@auth_bp.route("/reset", methods=["POST"])
def reset_password():
    """
    Reset password using email + reset code + new password.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""

    if not email or not code or not new_password:
        return (
            jsonify(
                {"message": "Email, code and new_password fields are all required"}
            ),
            400,
        )

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    ok, error = validate_password(new_password)
    if not ok:
        return jsonify({"message": error}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Invalid email or code"}), 400

    reset_obj = (
        PasswordResetCode.query.filter_by(user_id=user.id, code=code)
        .order_by(PasswordResetCode.created_at.desc())
        .first()
    )

    if not reset_obj or reset_obj.expires_at < datetime.utcnow():
        return jsonify({"message": "Reset code is invalid or has expired"}), 400

    user.password_hash = hash_password(new_password)
    PasswordResetCode.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({"message": "Password has been reset successfully"}), 200

