from flask import render_template, jsonify, request, flash, redirect, url_for, send_from_directory
from flask_login import login_required, current_user
from decimal import Decimal
from src import db
from src.tutor import tutor_bp
from src.auth.models import TutorDocument, Course, CourseStudent, CourseRequest, course_tutors, User
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
    valid_sections = ['dashboard', 'profile', 'courses', 'students', 'verification', 'settings']
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


# ==================== COURSE MANAGEMENT ROUTES ====================

@tutor_bp.route('/api/courses')
@login_required
def list_assigned_courses():
    """API endpoint to list courses assigned to the authenticated tutor."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get courses where tutor is assigned
        courses = Course.query.join(course_tutors).filter(
            course_tutors.c.tutor_id == current_user.id
        ).order_by(Course.created_at.desc()).all()
        
        courses_data = []
        for course in courses:
            # Get student count
            student_count = CourseStudent.query.filter_by(course_id=course.id, status='enrolled').count()
            # Get pending requests count
            pending_requests = CourseRequest.query.filter_by(
                course_id=course.id,
                tutor_id=current_user.id,
                status='pending'
            ).count()
            
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'description': course.description or '',
                'created_at': course.created_at.isoformat() if course.created_at else None,
                'student_count': student_count,
                'pending_requests': pending_requests
            })
        
        return jsonify({'success': True, 'courses': courses_data}), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception("Error listing assigned courses")
        return jsonify({'success': False, 'error': 'Failed to load courses'}), 500


@tutor_bp.route('/api/courses/<int:course_id>/view', methods=['GET'])
@login_required
def get_course_view(course_id):
    """API endpoint to get course view HTML content for dashboard."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Get enrolled students
        enrollments = CourseStudent.query.filter_by(course_id=course_id, status='enrolled').all()
        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            if student:
                students_data.append({
                    'id': student.id,
                    'full_name': student.full_name,
                    'email': student.email,
                    'disability_type': student.disability_type
                })
        
        # Get requests
        requests = CourseRequest.query.filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).order_by(CourseRequest.requested_at.desc()).all()
        
        requests_data = []
        for req in requests:
            student = req.student
            if student:
                requests_data.append({
                    'id': req.id,
                    'student_id': student.id,
                    'student_name': student.full_name,
                    'student_email': student.email,
                    'disability_type': student.disability_type,
                    'status': req.status,
                    'requested_at': req.requested_at.isoformat() if req.requested_at else None,
                    'responded_at': req.responded_at.isoformat() if req.responded_at else None
                })
        
        # Render course view template
        html = render_template('tutor/course_view.html', 
                              course=course, 
                              students=students_data, 
                              requests=requests_data,
                              course_id=course_id)
        
        return jsonify({'success': True, 'html': html}), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting course view for {course_id}")
        return jsonify({'success': False, 'error': 'Failed to load course: ' + str(e)}), 500


@tutor_bp.route('/api/courses/<int:course_id>')
@login_required
def get_course_details(course_id):
    """API endpoint to get course details for assigned tutor."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Get enrolled students
        enrollments = CourseStudent.query.filter_by(course_id=course_id, status='enrolled').all()
        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            if student:
                students_data.append({
                    'id': student.id,
                    'full_name': student.full_name,
                    'email': student.email,
                    'disability_type': student.disability_type
                })
        
        return jsonify({
            'success': True,
            'course': {
                'id': course.id,
                'name': course.name,
                'description': course.description or '',
                'students': students_data
            }
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting course details for {course_id}")
        return jsonify({'success': False, 'error': 'Failed to load course details'}), 500


@tutor_bp.route('/api/courses/<int:course_id>/requests')
@login_required
def get_course_requests(course_id):
    """API endpoint to get student requests for a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        # Get requests for this tutor
        requests = CourseRequest.query.filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).order_by(CourseRequest.requested_at.desc()).all()
        
        requests_data = []
        for req in requests:
            student = req.student
            if student:
                requests_data.append({
                    'id': req.id,
                    'student_id': student.id,
                    'student_name': student.full_name,
                    'student_email': student.email,
                    'disability_type': student.disability_type,
                    'status': req.status,
                    'requested_at': req.requested_at.isoformat() if req.requested_at else None,
                    'responded_at': req.responded_at.isoformat() if req.responded_at else None
                })
        
        return jsonify({'success': True, 'requests': requests_data}), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting course requests for {course_id}")
        return jsonify({'success': False, 'error': 'Failed to load requests'}), 500


@tutor_bp.route('/api/courses/<int:course_id>/requests/<int:request_id>', methods=['POST'])
@login_required
def respond_to_request(course_id, request_id):
    """API endpoint to accept or reject a student request."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        # Get request
        req = CourseRequest.query.filter_by(
            id=request_id,
            course_id=course_id,
            tutor_id=current_user.id
        ).first_or_404()
        
        if req.status != 'pending':
            return jsonify({'success': False, 'error': 'Request already processed'}), 400
        
        data = request.get_json()
        action = data.get('action')  # 'accept' or 'reject'
        
        if action not in ['accept', 'reject']:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        from datetime import datetime
        req.status = 'accepted' if action == 'accept' else 'rejected'
        req.responded_at = datetime.utcnow()
        
        # If accepted, create enrollment
        if action == 'accept':
            # Check if already enrolled
            existing = CourseStudent.query.filter_by(
                course_id=course_id,
                student_id=req.student_id
            ).first()
            
            if not existing:
                enrollment = CourseStudent(
                    course_id=course_id,
                    student_id=req.student_id,
                    status='enrolled',
                    assigned_by=current_user.id
                )
                db.session.add(enrollment)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Request {action}ed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error responding to request {request_id}")
        return jsonify({'success': False, 'error': 'Failed to process request'}), 500


@tutor_bp.route('/api/courses/<int:course_id>/students', methods=['POST'])
@login_required
def assign_students_to_course(course_id):
    """API endpoint for tutor to assign students to a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        disability_type = data.get('disability_type')  # Optional filter
        
        if not student_ids:
            return jsonify({'success': False, 'error': 'At least one student ID is required'}), 400
        
        assigned_count = 0
        for student_id in student_ids:
            student = User.query.filter_by(id=student_id, user_type='student').first()
            if not student:
                continue
            
            # Filter by disability type if specified
            if disability_type and student.disability_type != disability_type:
                continue
            
            # Check if already enrolled
            existing = CourseStudent.query.filter_by(
                course_id=course_id,
                student_id=student_id
            ).first()
            
            if not existing:
                enrollment = CourseStudent(
                    course_id=course_id,
                    student_id=student_id,
                    status='enrolled',
                    assigned_by=current_user.id
                )
                db.session.add(enrollment)
                assigned_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Assigned {assigned_count} student(s) to course'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error assigning students to course {course_id}")
        return jsonify({'success': False, 'error': 'Failed to assign students'}), 500


@tutor_bp.route('/api/courses/<int:course_id>/students/<int:student_id>', methods=['DELETE'])
@login_required
def remove_student_from_course(course_id, student_id):
    """API endpoint for tutor to remove a student from a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        # Find enrollment
        enrollment = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=student_id
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'Enrollment not found'}), 404
        
        db.session.delete(enrollment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Student removed from course'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error removing student {student_id} from course {course_id}")
        return jsonify({'success': False, 'error': 'Failed to remove student'}), 500