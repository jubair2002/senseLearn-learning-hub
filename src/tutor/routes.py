from flask import render_template, jsonify, request, flash, redirect, url_for, send_from_directory
from flask_login import login_required, current_user
from decimal import Decimal
from src import db
from src.tutor import tutor_bp
from src.auth.models import TutorDocument
from src.common.file_utils import save_uploaded_file, delete_file, get_file_url
from src.config import config
import os

@tutor_bp.route('/dashboard')
@tutor_bp.route('/dashboard/<section>')
@login_required
def dashboard(section=None):
    """Tutor dashboard page with optional section."""
    # Check if user is actually a tutor
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        flash('This page is only for tutors.', 'error')
        return redirect(url_for('index'))
    
    # Validate section name
    valid_sections = ['dashboard', 'profile', 'students', 'verification', 'settings']
    if section and section not in valid_sections:
        section = 'dashboard'
    elif not section:
        section = 'dashboard'
    
    return render_template('tutor/dashboard.html', user=current_user, default_section=section)

@tutor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Tutor profile page."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        flash('This page is only for tutors.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Check if this is an AJAX request first
        accept_header = request.headers.get('Accept', '')
        content_type = request.headers.get('Content-Type', '')
        is_ajax = (
            'application/json' in accept_header or 
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            'application/json' in content_type
        )
        
        # Get data from JSON or form data
        if 'application/json' in content_type:
            try:
                json_data = request.get_json() or {}
                full_name = json_data.get('full_name', '').strip()
                phone_number = json_data.get('phone_number', '').strip() or None
                qualifications = json_data.get('qualifications', '').strip()
                experience_years = json_data.get('experience_years', '0').strip()
                subjects = json_data.get('subjects', '').strip()
                hourly_rate = json_data.get('hourly_rate', '0').strip()
                bio = json_data.get('bio', '').strip()
            except Exception:
                # Fallback to form data if JSON parsing fails
                full_name = request.form.get('full_name', '').strip()
                phone_number = request.form.get('phone_number', '').strip() or None
                qualifications = request.form.get('qualifications', '').strip()
                experience_years = request.form.get('experience_years', '0').strip()
                subjects = request.form.get('subjects', '').strip()
                hourly_rate = request.form.get('hourly_rate', '0').strip()
                bio = request.form.get('bio', '').strip()
        else:
            full_name = request.form.get('full_name', '').strip()
            phone_number = request.form.get('phone_number', '').strip() or None
            qualifications = request.form.get('qualifications', '').strip()
            experience_years = request.form.get('experience_years', '0').strip()
            subjects = request.form.get('subjects', '').strip()
            hourly_rate = request.form.get('hourly_rate', '0').strip()
            bio = request.form.get('bio', '').strip()
        
        # Validation
        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not qualifications:
            errors.append('Qualifications are required.')
        if not experience_years or not experience_years.isdigit():
            errors.append('Valid experience years are required.')
        if not subjects:
            errors.append('Subjects are required.')
        if not hourly_rate:
            errors.append('Hourly rate is required.')
        if not bio:
            errors.append('Bio is required.')
        
        if errors:
            error_msg = ' '.join(errors)
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('tutor.profile'))
        
        try:
            # Use direct assignment (faster than merge for existing objects)
            current_user.full_name = full_name
            current_user.phone_number = phone_number
            current_user.qualifications = qualifications
            current_user.experience_years = int(experience_years)
            current_user.subjects = subjects
            current_user.hourly_rate = Decimal(hourly_rate)
            current_user.bio = bio
            # Flush before commit to catch errors early
            db.session.flush()
            db.session.commit()
            
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully!',
                    'data': {
                        'full_name': full_name,
                        'phone_number': phone_number or '',
                        'qualifications': qualifications,
                        'experience_years': int(experience_years),
                        'subjects': subjects,
                        'hourly_rate': str(hourly_rate),
                        'bio': bio
                    }
                }), 200
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('tutor.profile'))
        except Exception as e:
            if is_ajax:
                return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('tutor.profile'))
    
    return render_template('tutor/profile.html', user=current_user)

@tutor_bp.route('/verification')
@login_required
def verification():
    """Tutor verification page."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        flash('This page is only for tutors.', 'error')
        return redirect(url_for('index'))
    
    return render_template('tutor/verification.html', user=current_user)

@tutor_bp.route('/api/documents', methods=['GET'])
@login_required
def get_documents():
    """API endpoint to get all documents for the authenticated tutor."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Optimized query: select only needed columns, use index on tutor_id + uploaded_at
        documents = TutorDocument.query.filter_by(tutor_id=current_user.id)\
            .order_by(TutorDocument.uploaded_at.desc())\
            .with_entities(
                TutorDocument.id,
                TutorDocument.file_name,
                TutorDocument.file_type,
                TutorDocument.file_size,
                TutorDocument.mime_type,
                TutorDocument.uploaded_at,
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
            'file_url': get_file_url(doc.file_path)
        } for doc in documents]
        
        response = jsonify({'success': True, 'documents': docs_data})
        # Add caching headers
        response.cache_control.max_age = 60  # Cache for 60 seconds
        response.cache_control.private = True
        return response, 200
    except Exception as e:
        current_app.logger.exception("Error fetching documents")
        return jsonify({'success': False, 'error': 'Failed to load documents'}), 500


@tutor_bp.route('/api/documents', methods=['POST'])
@login_required
def upload_document():
    """API endpoint to upload a new document."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'certificate')
        
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save file
        result = save_uploaded_file(file, current_user.id)
        if not result:
            return jsonify({'success': False, 'error': 'Invalid file or file too large'}), 400
        
        file_path, original_filename, file_size, mime_type = result
        
        # Create document record
        doc = TutorDocument(
            tutor_id=current_user.id,
            file_name=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by_admin=False
        )
        db.session.add(doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document': {
                'id': doc.id,
                'file_name': doc.file_name,
                'file_type': doc.file_type,
                'file_url': get_file_url(doc.file_path)
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@tutor_bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    """API endpoint to delete a document."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        doc = TutorDocument.query.filter_by(id=doc_id, tutor_id=current_user.id).first()
        if not doc:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        # Delete file from filesystem
        delete_file(doc.file_path)
        
        # Delete record
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Document deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@tutor_bp.route('/api/stats')
@login_required
def get_stats():
    """
    API endpoint for tutor dashboard stats.
    Returns statistics for the authenticated tutor.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # TODO: Implement actual database queries for statistics
    # This endpoint should query:
    # - Total students (distinct student_id from sessions where tutor_id = current_user.id)
    # - Total sessions (from sessions table where tutor_id = current_user.id)
    # - Upcoming sessions (sessions with status='scheduled' and date > now)
    # - Total earnings (sum of session payments from payments table)
    # - Average rating (from ratings table where tutor_id = current_user.id)
    # - Completion rate (percentage of completed sessions)
    
    # Return empty stats structure - to be implemented with actual queries
    stats = {
        'total_students': 0,
        'total_sessions': 0,
        'upcoming_sessions': 0,
        'total_earnings': 0.0,
        'avg_rating': 0.0,
        'completion_rate': 0
    }
    return jsonify(stats)