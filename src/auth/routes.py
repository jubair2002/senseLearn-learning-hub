from datetime import datetime

from flask import current_app, jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src import db
from src.config import config
from src.auth import auth_bp
from src.auth.models import PasswordResetCode, User, EmailVerificationOTP, PendingRegistration
from src.auth.utils import (
    generate_reset_code,
    generate_otp,
    hash_password,
    is_valid_email,
    validate_password,
    verify_password,
)
from src.auth.email_service import send_otp_email


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
                f"{base_path}/verify-email",
                f"{base_path}/resend-otp",
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

        # Optimize: Check email first (most common case, has index), then username if provided
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"message": "User with this email already exists"}), 409
        
        if username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return jsonify({"message": "User with this username already exists"}), 409

        # Student-specific validation
        disability_type = None
        if user_type == "student":
            disability_type = (data.get("disability_type") or "").strip()
            if not disability_type:
                return jsonify({"message": "Disability type is required for students"}), 400
            
            if disability_type not in config.VALID_DISABILITY_TYPES:
                return jsonify({
                    "message": f"Invalid disability type. Must be one of: {', '.join(config.VALID_DISABILITY_TYPES)}"
                }), 400

        # Tutor-specific validation
        qualifications = None
        experience_years = None
        subjects = None
        hourly_rate = None
        bio = None
        
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

        # Store registration data temporarily (don't create user yet)
        # Bulk delete any existing pending registration for this email (faster)
        db.session.query(PendingRegistration).filter_by(email=email).delete(synchronize_session=False)
        
        # Prepare registration data
        registration_data = {
            "email": email,
            "password": password,  # Store password, will be hashed when creating user
            "full_name": full_name,
            "username": username,
            "phone_number": phone_number,
            "user_type": user_type,
            "disability_type": disability_type,
            "qualifications": qualifications,
            "experience_years": experience_years,
            "subjects": subjects,
            "hourly_rate": hourly_rate,
            "bio": bio,
        }
        
        pending_reg = PendingRegistration.create(
            email=email,
            registration_data=registration_data,
            minutes_valid=30  # Pending registration expires in 30 minutes
        )
        db.session.add(pending_reg)
        db.session.flush()
        
        # Generate and send OTP for email verification
        otp = generate_otp(length=config.OTP_LENGTH)
        verification_otp = EmailVerificationOTP.create_for_email(
            email,
            otp,
            minutes_valid=config.OTP_VALIDITY_MINUTES,
            purpose="verification"
        )
        db.session.add(verification_otp)
        
        # Commit first (fast operation)
        db.session.commit()
        
        # Send OTP email in background (non-blocking, faster API response)
        send_otp_email(email, otp, purpose="verification", async_send=True)
        # Email is sent in background, we return success immediately
        
        # Success message - user needs to verify email to complete registration
        success_message = f"Please check your email ({email}) for the verification OTP to complete your registration."
        
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
        "email_verification_required": True,
        "email": email
    }), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    remember = data.get("remember", False)  # Default to False if not provided

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    # Optimize query - only select needed fields for login check (faster than full object)
    user_result = db.session.query(
        User.id, User.email, User.password_hash, User.full_name, 
        User.user_type, User.email_verified, User.is_verified
    ).filter_by(email=email).first()
    
    if not user_result:
        return jsonify({"message": "Invalid email or password"}), 401
    
    # Verify password (fast operation)
    if not verify_password(password, user_result.password_hash):
        return jsonify({"message": "Invalid email or password"}), 401
    
    # Load full user object for login_user using identity map (very fast - no query if already loaded)
    user = db.session.get(User, user_result.id)

    # Login the user with remember me option
    login_user(user, remember=remember)
    
    # Return success with user info
    return jsonify({
        "message": config.MSG_LOGIN_SUCCESS,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user.user_type,
            "email_verified": user.email_verified,
            "is_verified": user.is_verified if hasattr(user, 'is_verified') else True
        }
    }), 200


@auth_bp.route("/logout")
@login_required
def logout_route():
    """Logout route."""
    from flask import redirect, url_for
    logout_user()
    return redirect(url_for('login_page'))


@auth_bp.route("/forgot", methods=["POST"])
def forgot_password():
    """
    Generate and send OTP via email for password reset.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal if user exists or not for security
        return jsonify({
            "message": "If an account exists with this email, a password reset OTP has been sent."
        }), 200

    # Bulk delete old OTPs for this user (faster than individual deletes)
    db.session.query(EmailVerificationOTP).filter_by(
        user_id=user.id, 
        purpose="password_reset"
    ).delete(synchronize_session=False)
    db.session.query(PasswordResetCode).filter_by(user_id=user.id).delete(synchronize_session=False)

    # Generate OTP
    otp = generate_otp(length=config.OTP_LENGTH)
    reset_otp = EmailVerificationOTP.create_for_user(
        user,
        otp,
        minutes_valid=config.OTP_VALIDITY_MINUTES,
        purpose="password_reset"
    )
    db.session.add(reset_otp)
    db.session.commit()
    
    # Send OTP email in background (non-blocking, faster API response)
    send_otp_email(user.email, otp, purpose="password_reset", async_send=True)

    return jsonify({
        "message": "If an account exists with this email, a password reset OTP has been sent.",
        "expires_in_minutes": config.OTP_VALIDITY_MINUTES
    }), 200


@auth_bp.route("/reset", methods=["POST"])
def reset_password():
    """
    Reset password using email + OTP + new password.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or data.get("code") or "").strip()  # Support both 'otp' and 'code' for backward compatibility
    new_password = data.get("new_password") or ""

    if not email or not otp or not new_password:
        return (
            jsonify(
                {"message": "Email, OTP and new_password fields are all required"}
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
        return jsonify({"message": "Invalid email or OTP"}), 400

    # Check EmailVerificationOTP first (new method)
    reset_otp = (
        EmailVerificationOTP.query.filter_by(
            user_id=user.id, 
            otp=otp,
            purpose="password_reset"
        )
        .order_by(EmailVerificationOTP.created_at.desc())
        .first()
    )

    # Fallback to PasswordResetCode for backward compatibility
    if not reset_otp:
        reset_obj = (
            PasswordResetCode.query.filter_by(user_id=user.id, code=otp)
            .order_by(PasswordResetCode.created_at.desc())
            .first()
        )
        if reset_obj and reset_obj.expires_at >= datetime.utcnow():
            # Valid old-style reset code
            user.password_hash = hash_password(new_password)
            PasswordResetCode.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            return jsonify({"message": config.MSG_PASSWORD_RESET_SUCCESS}), 200
    else:
        # Check if OTP is expired
        if reset_otp.expires_at < datetime.utcnow():
            return jsonify({"message": "OTP is invalid or has expired"}), 400
        
        # Valid OTP - bulk delete old OTPs
        user.password_hash = hash_password(new_password)
        db.session.query(EmailVerificationOTP).filter_by(user_id=user.id, purpose="password_reset").delete(synchronize_session=False)
        db.session.query(PasswordResetCode).filter_by(user_id=user.id).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"message": config.MSG_PASSWORD_RESET_SUCCESS}), 200

    return jsonify({"message": "OTP is invalid or has expired"}), 400


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """
    Verify email address using OTP sent during registration.
    Creates the user account after successful OTP verification.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return jsonify({"message": "Email and OTP are required"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    # Check if user already exists (might be from old flow)
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        if existing_user.email_verified:
            return jsonify({"message": "Email is already verified"}), 400
        
        # Old flow: user exists but not verified
        verification_otp = (
            EmailVerificationOTP.query.filter_by(
                user_id=existing_user.id,
                otp=otp,
                purpose="verification"
            )
            .order_by(EmailVerificationOTP.created_at.desc())
            .first()
        )
        
        if verification_otp and verification_otp.expires_at >= datetime.utcnow():
            existing_user.email_verified = True
            db.session.query(EmailVerificationOTP).filter_by(user_id=existing_user.id, purpose="verification").delete(synchronize_session=False)
            db.session.commit()
            login_user(existing_user, remember=True)
            return jsonify({
                "message": "Email verified successfully!",
                "user": {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "full_name": existing_user.full_name,
                    "user_type": existing_user.user_type,
                    "email_verified": True,
                    "is_verified": existing_user.is_verified if hasattr(existing_user, 'is_verified') else True
                }
            }), 200

    # New flow: Check for pending registration
    pending_reg = PendingRegistration.query.filter_by(email=email).first()
    if not pending_reg:
        return jsonify({"message": "No pending registration found. Please register first."}), 400

    if pending_reg.expires_at < datetime.utcnow():
        # Bulk delete expired pending registration and OTP (faster)
        db.session.query(PendingRegistration).filter_by(email=email).delete(synchronize_session=False)
        db.session.query(EmailVerificationOTP).filter_by(email=email, purpose="verification").delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"message": "Registration session expired. Please register again."}), 400

    # Verify OTP
    verification_otp = (
        EmailVerificationOTP.query.filter_by(
            email=email,
            otp=otp,
            purpose="verification"
        )
        .order_by(EmailVerificationOTP.created_at.desc())
        .first()
    )

    if not verification_otp:
        return jsonify({"message": "Invalid OTP"}), 400

    if verification_otp.expires_at < datetime.utcnow():
        return jsonify({"message": "OTP has expired. Please request a new one."}), 400

    # Get registration data
    reg_data = pending_reg.get_registration_data()
    
    # Check again if user exists (race condition)
    user = User.query.filter_by(email=email).first()
    if user:
        # Bulk delete (faster)
        db.session.query(PendingRegistration).filter_by(email=email).delete(synchronize_session=False)
        db.session.query(EmailVerificationOTP).filter_by(email=email, purpose="verification").delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"message": "User already exists. Please login instead."}), 409

    # Create the user account
    try:
        user = User(
            email=email,
            password_hash=hash_password(reg_data["password"]),
            full_name=reg_data["full_name"],
            username=reg_data["username"],
            phone_number=reg_data["phone_number"],
            user_type=reg_data["user_type"],
            email_verified=True,  # Email verified now
        )

        # Set student-specific fields
        if reg_data["user_type"] == "student" and reg_data["disability_type"]:
            user.disability_type = reg_data["disability_type"]

        # Set tutor-specific fields
        if reg_data["user_type"] == "tutor":
            user.qualifications = reg_data["qualifications"]
            user.experience_years = int(reg_data["experience_years"])
            user.subjects = reg_data["subjects"]
            user.hourly_rate = reg_data["hourly_rate"]
            user.bio = reg_data["bio"]
            user.is_verified = False  # Tutors need admin verification

        db.session.add(user)
        
        # Bulk delete pending registration and OTP (faster)
        db.session.query(PendingRegistration).filter_by(email=email).delete(synchronize_session=False)
        db.session.query(EmailVerificationOTP).filter_by(email=email, purpose="verification").delete(synchronize_session=False)
        
        db.session.commit()

        # Auto-login the user after successful registration
        login_user(user, remember=True)

        success_message = {
            "student": config.MSG_STUDENT_REGISTER_SUCCESS,
            "tutor": config.MSG_TUTOR_REGISTER_SUCCESS
        }.get(reg_data["user_type"], "Account created successfully!")

        return jsonify({
            "message": success_message,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "user_type": user.user_type,
                "email_verified": True,
                "is_verified": user.is_verified if hasattr(user, 'is_verified') else True
            }
        }), 201
        
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.exception("Error while creating user after verification")
        return jsonify({
            "message": "Failed to create account. Please try registering again."
        }), 500


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    """
    Resend OTP for email verification or password reset.
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    purpose = (data.get("purpose") or "verification").strip().lower()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Please provide a valid email address"}), 400

    if purpose not in ["verification", "password_reset"]:
        return jsonify({"message": "Purpose must be 'verification' or 'password_reset'"}), 400

    # For password reset, check if user exists
    if purpose == "password_reset":
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                "message": "If an account exists with this email, an OTP has been sent."
            }), 200

        # Bulk delete old OTPs (faster)
        db.session.query(EmailVerificationOTP).filter_by(
            user_id=user.id,
            purpose=purpose
        ).delete(synchronize_session=False)
        db.session.flush()

        # Generate new OTP
        otp = generate_otp(length=config.OTP_LENGTH)
        new_otp = EmailVerificationOTP.create_for_user(
            user,
            otp,
            minutes_valid=config.OTP_VALIDITY_MINUTES,
            purpose=purpose
        )
        db.session.add(new_otp)
        db.session.commit()
        
        # Send OTP email in background (non-blocking)
        send_otp_email(email, otp, purpose=purpose, async_send=True)
        
        return jsonify({
            "message": "If an account exists with this email, an OTP has been sent.",
            "expires_in_minutes": config.OTP_VALIDITY_MINUTES
        }), 200

    # For verification, check pending registration or existing user
    if purpose == "verification":
        # Check pending registration first
        pending_reg = PendingRegistration.query.filter_by(email=email).first()
        if pending_reg:
            if pending_reg.expires_at < datetime.utcnow():
                # Bulk delete (faster)
                db.session.query(PendingRegistration).filter_by(email=email).delete(synchronize_session=False)
                db.session.query(EmailVerificationOTP).filter_by(email=email, purpose="verification").delete(synchronize_session=False)
                db.session.commit()
                return jsonify({"message": "Registration session expired. Please register again."}), 400
            
            # Bulk delete old OTPs for this email (faster)
            db.session.query(EmailVerificationOTP).filter_by(email=email, purpose="verification").delete(synchronize_session=False)
            db.session.flush()

            # Generate new OTP
            otp = generate_otp(length=config.OTP_LENGTH)
            new_otp = EmailVerificationOTP.create_for_email(
                email,
                otp,
                minutes_valid=config.OTP_VALIDITY_MINUTES,
                purpose="verification"
            )
            db.session.add(new_otp)
            db.session.commit()

            # Send OTP email in background (non-blocking)
            send_otp_email(email, otp, purpose="verification", async_send=True)
            
            return jsonify({
                "message": "OTP has been resent to your email.",
                "expires_in_minutes": config.OTP_VALIDITY_MINUTES
            }), 200

        # Check if user exists but not verified
        user = User.query.filter_by(email=email).first()
        if user:
            if user.email_verified:
                return jsonify({"message": "Email is already verified"}), 400

            # Bulk delete old OTPs (faster)
            db.session.query(EmailVerificationOTP).filter_by(
                user_id=user.id,
                purpose="verification"
            ).delete(synchronize_session=False)
            db.session.flush()

            # Generate new OTP
            otp = generate_otp(length=config.OTP_LENGTH)
            new_otp = EmailVerificationOTP.create_for_user(
                user,
                otp,
                minutes_valid=config.OTP_VALIDITY_MINUTES,
                purpose="verification"
            )
            db.session.add(new_otp)
            db.session.commit()

            # Send OTP email in background (non-blocking)
            send_otp_email(email, otp, purpose="verification", async_send=True)
            
            return jsonify({
                "message": "OTP has been resent to your email.",
                "expires_in_minutes": config.OTP_VALIDITY_MINUTES
            }), 200

        # No pending registration or user found
        return jsonify({
            "message": "No pending registration found. Please register first."
        }), 400