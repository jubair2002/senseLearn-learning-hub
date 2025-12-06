from datetime import datetime

from flask import current_app, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from src import db
from src.config import config
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
    """Simple health/info endpoint for auth API."""
    base_path = config.AUTH_API_PREFIX
    return jsonify(
        {
            "status": "ok",
            "message": "Auth API is running",
            "endpoints": [
                f"{base_path}/register",
                f"{base_path}/login",
                f"{base_path}/forgot",
                f"{base_path}/reset",
            ],
        }
    ), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        
        # Common fields
        full_name = (data.get("full_name") or "").strip()
        user_type = (data.get("user_type") or config.DEFAULT_USER_TYPE).strip().lower()
        
        # Optional common fields
        username = (data.get("username") or "").strip() or None
        phone_number = (data.get("phone_number") or "").strip() or None

        # Validate required fields
        if not email or not password or not full_name:
            return jsonify(
                {"message": "Email, password, and full_name are required"}
            ), 400

        if not is_valid_email(email):
            return jsonify({"message": "Please provide a valid email address"}), 400

        # Validate user type
        if user_type not in config.VALID_USER_TYPES:
            return jsonify({
                "message": f"Invalid user type. Must be one of: {', '.join(config.VALID_USER_TYPES)}"
            }), 400

        ok, error = validate_password(password)
        if not ok:
            return jsonify({"message": error}), 400

        # Check for existing email
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "User with this email already exists"}), 409
        
        # Check for existing username if provided
        if username and User.query.filter_by(username=username).first():
            return jsonify({"message": "User with this username already exists"}), 409

        # Student-specific validation
        if user_type == "student":
            disability_type = (data.get("disability_type") or "").strip()
            if not disability_type:
                return jsonify({"message": "Disability type is required for students"}), 400
            
            if disability_type not in config.VALID_DISABILITY_TYPES:
                return jsonify({
                    "message": f"Invalid disability type. Must be one of: {', '.join(config.VALID_DISABILITY_TYPES)}"
                }), 400

        # Tutor-specific validation
        if user_type == "tutor":
            qualifications = (data.get("qualifications") or "").strip()
            experience_years = data.get("experience_years")
            subjects = (data.get("subjects") or "").strip()
            hourly_rate = data.get("hourly_rate")
            bio = (data.get("bio") or "").strip()
            
            # Validate required tutor fields
            if not qualifications or not subjects or not bio:
                return jsonify({"message": "Qualifications, subjects, and bio are required for tutors"}), 400
            
            if experience_years is None or experience_years < 0:
                return jsonify({"message": "Valid years of experience required for tutors"}), 400
            
            if hourly_rate is None or float(hourly_rate) <= 0:
                return jsonify({"message": "Valid hourly rate required for tutors"}), 400

        # Create user with appropriate fields
        user = User(
            email=email, 
            password_hash=hash_password(password),
            full_name=full_name,
            username=username,
            phone_number=phone_number,
            user_type=user_type,
        )

        # Set student-specific fields
        if user_type == "student":
            user.disability_type = disability_type
        
        # Set tutor-specific fields
        if user_type == "tutor":
            user.qualifications = qualifications
            user.experience_years = int(experience_years)
            user.subjects = subjects
            user.hourly_rate = hourly_rate
            user.bio = bio
            user.is_verified = False  # Tutors need verification

        db.session.add(user)
        db.session.commit()
        
        # Login the user after registration
        login_user(user, remember=True)
        
        # Prepare success message based on user type
        success_message = {
            "student": config.MSG_STUDENT_REGISTER_SUCCESS,
            "tutor": config.MSG_TUTOR_REGISTER_SUCCESS
        }.get(user_type, "Account created successfully!")
        
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

    return jsonify({
        "message": success_message, 
        "user_type": user_type,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user.user_type,
            "is_verified": user.is_verified if hasattr(user, 'is_verified') else True
        }
    }), 201


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

    # Login the user
    login_user(user, remember=True)
    
    # Return success with user info
    return jsonify({
        "message": config.MSG_LOGIN_SUCCESS,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user.user_type,
            "is_verified": user.is_verified if hasattr(user, 'is_verified') else True
        }
    }), 200


@auth_bp.route("/logout")
@login_required
def logout_route():
    """Logout route."""
    logout_user()
    return jsonify({"message": config.MSG_LOGOUT_SUCCESS}), 200


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

    code = generate_reset_code(length=config.RESET_CODE_LENGTH)
    reset_obj = PasswordResetCode.create_for_user(
        user, 
        code, 
        minutes_valid=config.RESET_CODE_VALIDITY_MINUTES
    )
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

    return jsonify({"message": config.MSG_PASSWORD_RESET_SUCCESS}), 200