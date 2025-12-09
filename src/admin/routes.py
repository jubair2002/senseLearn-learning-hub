"""Admin routes for managing users and verifying tutors."""
import secrets
import string
from flask import render_template, jsonify, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from decimal import Decimal

from src import db
from src.admin import admin_bp
from src.auth.models import User, TutorDocument
from src.auth.utils import hash_password, is_valid_email, validate_password
from src.auth.email_service import send_credentials_email
from src.common.decorators import admin_required
from src.common.file_utils import save_uploaded_file, get_file_url
from src.config import config
import os


def generate_random_password(length: int = 12) -> str:
    """Generate a random secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@admin_bp.route('/dashboard')
@admin_bp.route('/dashboard/<section>')
@login_required
@admin_required
def dashboard(section=None):
    """Admin dashboard page with optional section."""
    # Validate section name
    valid_sections = ['dashboard', 'tutors', 'students', 'create-account', 'settings']
    if section and section not in valid_sections:
        section = 'dashboard'
    elif not section:
        section = 'dashboard'
    
    return render_template('admin/dashboard.html', user=current_user, default_section=section)


@admin_bp.route('/api/tutors')
@login_required
@admin_required
def list_tutors():
    """API endpoint to list all tutors with their verification status and document count."""
    try:
        from sqlalchemy import func
        
        # Optimized: Use subquery to count documents in one query instead of N+1
        doc_counts = db.session.query(
            TutorDocument.tutor_id,
            func.count(TutorDocument.id).label('doc_count')
        ).group_by(TutorDocument.tutor_id).subquery()
        
        # Optimized query: select only needed columns, left join document counts
        tutors = db.session.query(
            User.id,
            User.email,
            User.full_name,
            User.username,
            User.phone_number,
            User.qualifications,
            User.experience_years,
            User.subjects,
            User.hourly_rate,
            User.bio,
            User.is_verified,
            User.email_verified,
            User.created_at,
            func.coalesce(doc_counts.c.doc_count, 0).label('document_count')
        ).filter_by(user_type='tutor')\
         .outerjoin(doc_counts, User.id == doc_counts.c.tutor_id)\
         .order_by(User.created_at.desc())\
         .all()
        
        # Use list comprehension for faster data building
        tutors_data = [{
            'id': tutor.id,
            'email': tutor.email,
            'full_name': tutor.full_name,
            'username': tutor.username or '',
            'phone_number': tutor.phone_number or '',
            'qualifications': tutor.qualifications or '',
            'experience_years': tutor.experience_years or 0,
            'subjects': tutor.subjects or '',
            'hourly_rate': str(tutor.hourly_rate) if tutor.hourly_rate else '0',
            'bio': tutor.bio or '',
            'is_verified': tutor.is_verified if hasattr(tutor, 'is_verified') else False,
            'email_verified': tutor.email_verified if hasattr(tutor, 'email_verified') else False,
            'created_at': tutor.created_at.isoformat() if tutor.created_at else None,
            'document_count': int(tutor.document_count)
        } for tutor in tutors]
        
        response = jsonify({'success': True, 'tutors': tutors_data})
        # Add caching headers
        response.cache_control.max_age = 30  # Cache for 30 seconds
        response.cache_control.private = True
        return response, 200
    except Exception as e:
        current_app.logger.exception("Error fetching tutors")
        return jsonify({'success': False, 'error': 'Failed to load tutors'}), 500


@admin_bp.route('/api/tutors/<int:tutor_id>/documents')
@login_required
@admin_required
def get_tutor_documents(tutor_id):
    """API endpoint to get all documents for a specific tutor."""
    try:
        # Optimized: Check tutor exists with minimal query
        tutor_exists = db.session.query(User.id).filter_by(id=tutor_id, user_type='tutor').first()
        if not tutor_exists:
            return jsonify({'success': False, 'error': 'Tutor not found'}), 404
        
        # Optimized query: select only needed columns
        documents = TutorDocument.query.filter_by(tutor_id=tutor_id)\
            .order_by(TutorDocument.uploaded_at.desc())\
            .with_entities(
                TutorDocument.id,
                TutorDocument.file_name,
                TutorDocument.file_type,
                TutorDocument.file_size,
                TutorDocument.mime_type,
                TutorDocument.uploaded_at,
                TutorDocument.uploaded_by_admin,
                TutorDocument.file_path
            ).all()
        
        # Use list comprehension for faster data building
        docs_data = [{
            'id': doc.id,
            'file_name': doc.file_name,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'mime_type': doc.mime_type,
            'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            'uploaded_by_admin': doc.uploaded_by_admin,
            'file_url': get_file_url(doc.file_path)
        } for doc in documents]
        
        response = jsonify({'success': True, 'documents': docs_data})
        # Add caching headers
        response.cache_control.max_age = 60
        response.cache_control.private = True
        return response, 200
    except Exception as e:
        current_app.logger.exception("Error fetching tutor documents")
        return jsonify({'success': False, 'error': 'Failed to load documents'}), 500


@admin_bp.route('/api/students')
@login_required
@admin_required
def list_students():
    """API endpoint to list all students."""
    try:
        students = User.query.filter_by(user_type='student').order_by(User.created_at.desc()).all()
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'email': student.email,
                'full_name': student.full_name,
                'username': student.username or '',
                'phone_number': student.phone_number or '',
                'disability_type': student.disability_type or '',
                'email_verified': student.email_verified if hasattr(student, 'email_verified') else False,
                'created_at': student.created_at.isoformat() if student.created_at else None
            })
        
        return jsonify({'success': True, 'students': students_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/verify-tutor', methods=['POST'])
@login_required
@admin_required
def verify_tutor():
    """API endpoint to verify or unverify a tutor."""
    try:
        data = request.get_json() or {}
        tutor_id = data.get('tutor_id')
        verify = data.get('verify', True)  # Default to True
        
        if not tutor_id:
            return jsonify({'success': False, 'error': 'Tutor ID is required'}), 400
        
        tutor = User.query.filter_by(id=tutor_id, user_type='tutor').first()
        if not tutor:
            return jsonify({'success': False, 'error': 'Tutor not found'}), 404
        
        tutor.is_verified = bool(verify)
        db.session.commit()
        
        action = 'verified' if verify else 'unverified'
        return jsonify({
            'success': True,
            'message': f'Tutor {action} successfully',
            'is_verified': tutor.is_verified
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/create-account', methods=['POST'])
@login_required
@admin_required
def create_account():
    """API endpoint to create a new student or tutor account."""
    try:
        # Handle both JSON and form-data (for file uploads)
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            files = request.files.getlist('documents[]')  # Get all uploaded files
        else:
            data = request.get_json() or {}
            files = []
        
        # Get user type
        user_type = (data.get('user_type') or '').strip().lower()
        if user_type not in ['student', 'tutor']:
            return jsonify({'success': False, 'error': 'Invalid user type. Must be student or tutor'}), 400
        
        # Get common fields
        email = (data.get('email') or '').strip().lower()
        full_name = (data.get('full_name') or '').strip()
        username = (data.get('username') or '').strip() or None
        phone_number = (data.get('phone_number') or '').strip() or None
        
        # Validation
        if not email or not full_name:
            return jsonify({'success': False, 'error': 'Email and full name are required'}), 400
        
        if not is_valid_email(email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'User with this email already exists'}), 409
        
        if username:
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                return jsonify({'success': False, 'error': 'Username already taken'}), 409
        
        # Generate password
        password = generate_random_password()
        password_hash = hash_password(password)
        
        # Create user object
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            username=username,
            phone_number=phone_number,
            user_type=user_type,
            email_verified=True  # Admin-created accounts are pre-verified
        )
        
        # Add user type specific fields
        if user_type == 'student':
            disability_type = (data.get('disability_type') or '').strip()
            if not disability_type:
                return jsonify({'success': False, 'error': 'Disability type is required for students'}), 400
            if disability_type not in config.VALID_DISABILITY_TYPES:
                return jsonify({
                    'success': False,
                    'error': f'Invalid disability type. Must be one of: {", ".join(config.VALID_DISABILITY_TYPES)}'
                }), 400
            user.disability_type = disability_type
            user.is_verified = True  # Students don't need verification
        
        elif user_type == 'tutor':
            qualifications = (data.get('qualifications') or '').strip()
            experience_years = data.get('experience_years')
            subjects = (data.get('subjects') or '').strip()
            hourly_rate = data.get('hourly_rate')
            bio = (data.get('bio') or '').strip()
            
            # Validate required tutor fields
            if not qualifications or not subjects or not bio:
                return jsonify({
                    'success': False,
                    'error': 'Qualifications, subjects, and bio are required for tutors'
                }), 400
            
            if experience_years is None or int(experience_years) < 0:
                return jsonify({
                    'success': False,
                    'error': 'Valid years of experience required for tutors'
                }), 400
            
            if hourly_rate is None or float(hourly_rate) <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Valid hourly rate required for tutors'
                }), 400
            
            user.qualifications = qualifications
            user.experience_years = int(experience_years)
            user.subjects = subjects
            user.hourly_rate = Decimal(str(hourly_rate))
            user.bio = bio
            user.is_verified = False  # Tutors need admin verification
        
        # Save to database
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Handle file uploads for tutors
        if user_type == 'tutor' and files:
            for idx, file in enumerate(files):
                if file and file.filename:
                    try:
                        # Save file
                        result = save_uploaded_file(file, user.id)
                        if result:
                            file_path, original_filename, file_size, mime_type = result
                            file_type = data.get(f'file_type_{idx}', 'certificate')
                            
                            # Create document record
                            doc = TutorDocument(
                                tutor_id=user.id,
                                file_name=original_filename,
                                file_path=file_path,
                                file_type=file_type,
                                file_size=file_size,
                                mime_type=mime_type,
                                uploaded_by_admin=True
                            )
                            db.session.add(doc)
                    except Exception as e:
                        # Log error but continue with account creation
                        current_app.logger.error(f"Error uploading file for tutor {user.id}: {str(e)}")
        
        # Send credentials email
        login_username = username or email
        send_credentials_email(
            to_email=email,
            username=login_username,
            password=password,
            user_type=user_type,
            async_send=True
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{user_type.capitalize()} account created successfully. Credentials have been sent to {email}',
            'user_id': user.id
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error creating account: {str(e)}'}), 500


@admin_bp.route('/api/stats')
@login_required
@admin_required
def get_stats():
    """API endpoint for admin dashboard statistics."""
    try:
        total_students = User.query.filter_by(user_type='student').count()
        total_tutors = User.query.filter_by(user_type='tutor').count()
        verified_tutors = User.query.filter_by(user_type='tutor', is_verified=True).count()
        pending_tutors = User.query.filter_by(user_type='tutor', is_verified=False).count()
        total_admins = User.query.filter_by(user_type='admin').count()
        
        stats = {
            'total_students': total_students,
            'total_tutors': total_tutors,
            'verified_tutors': verified_tutors,
            'pending_tutors': pending_tutors,
            'total_admins': total_admins
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

