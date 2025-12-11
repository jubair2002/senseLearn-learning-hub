from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from src import db
from src.student import student_bp
from src.auth.models import Course, CourseStudent, CourseRequest, course_tutors, User, CourseModule, ModuleFile, StudentFileProgress
from src.common.file_utils import get_file_url

@student_bp.route('/dashboard')
@student_bp.route('/dashboard/<section>')
@login_required
def dashboard(section=None):
    """Student dashboard page with optional section."""
    # Check if user is actually a student
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        flash('This page is only for students.', 'error')
        return redirect(url_for('index'))
    
    # Validate section name
    valid_sections = ['dashboard', 'profile', 'courses', 'tutors', 'sessions', 'progress', 'settings']
    if section and section not in valid_sections:
        section = 'dashboard'
    elif not section:
        section = 'dashboard'
    
    return render_template('student/dashboard.html', user=current_user, default_section=section)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Student profile page."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        flash('This page is only for students.', 'error')
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
                disability_type = json_data.get('disability_type', '').strip()
            except Exception:
                # Fallback to form data if JSON parsing fails
                full_name = request.form.get('full_name', '').strip()
                phone_number = request.form.get('phone_number', '').strip() or None
                disability_type = request.form.get('disability_type', '').strip()
        else:
            full_name = request.form.get('full_name', '').strip()
            phone_number = request.form.get('phone_number', '').strip() or None
            disability_type = request.form.get('disability_type', '').strip()
        
        
        if not full_name or not disability_type:
            error_msg = 'Full name and disability type are required.'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('student.profile'))
        
        try:
            # Use direct assignment (faster than merge for existing objects)
            current_user.full_name = full_name
            current_user.phone_number = phone_number
            current_user.disability_type = disability_type
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
                        'disability_type': disability_type
                    }
                }), 200
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student.profile'))
        except Exception as e:
            if is_ajax:
                return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('student.profile'))
    
    return render_template('student/profile.html', user=current_user)

@student_bp.route('/api/stats')
@login_required
def get_stats():
    """
    API endpoint for student dashboard stats.
    Returns statistics for the authenticated student.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # TODO: Implement actual database queries for statistics
    # This endpoint should query:
    # - Total sessions (from sessions table)
    # - Completed sessions (sessions with status='completed')
    # - Upcoming sessions (sessions with status='scheduled' and date > now)
    # - Hours learned (sum of session durations)
    # - Tutors count (distinct tutor_id from sessions)
    # - Average rating (from ratings table)
    
    # Return empty stats structure - to be implemented with actual queries
    stats = {
        'total_sessions': 0,
        'completed_sessions': 0,
        'upcoming_sessions': 0,
        'hours_learned': 0,
        'tutors_count': 0,
        'avg_rating': 0.0
    }
    return jsonify(stats)


# ==================== COURSE MANAGEMENT ROUTES ====================

@student_bp.route('/api/courses')
@login_required
def list_all_courses():
    """API endpoint to list all courses (students can see all courses)."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get search query parameter
        search_query = request.args.get('search', '').strip()
        
        # Build query
        query = Course.query
        
        # Apply search filter if provided
        if search_query:
            search_term = f'%{search_query}%'
            query = query.filter(
                db.or_(
                    Course.name.ilike(search_term),
                    Course.description.ilike(search_term)
                )
            )
        
        courses = query.order_by(Course.created_at.desc()).all()
        
        courses_data = []
        for course in courses:
            # Check if student is enrolled
            enrollment = CourseStudent.query.filter_by(
                course_id=course.id,
                student_id=current_user.id,
                status='enrolled'
            ).first()
            
            # Check if student has pending request
            pending_request = CourseRequest.query.filter_by(
                course_id=course.id,
                student_id=current_user.id,
                status='pending'
            ).first()
            
            # Get tutor count
            tutor_count = db.session.query(course_tutors).filter_by(course_id=course.id).count()
            # Get enrolled student count
            enrolled_count = CourseStudent.query.filter_by(course_id=course.id, status='enrolled').count()
            
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'description': course.description or '',
                'created_at': course.created_at.isoformat() if course.created_at else None,
                'tutor_count': tutor_count,
                'enrolled_count': enrolled_count,
                'is_enrolled': enrollment is not None,
                'has_pending_request': pending_request is not None
            })
        
        return jsonify({'success': True, 'courses': courses_data}), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception("Error listing courses")
        return jsonify({'success': False, 'error': 'Failed to load courses'}), 500


@student_bp.route('/api/courses/enrolled')
@login_required
def list_enrolled_courses():
    """API endpoint to list courses the student is enrolled in."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get search query parameter
        search_query = request.args.get('search', '').strip()
        
        # Build query with join to Course table for efficient search
        query = CourseStudent.query.join(Course, CourseStudent.course_id == Course.id).filter(
            CourseStudent.student_id == current_user.id,
            CourseStudent.status == 'enrolled'
        )
        
        # Apply search filter at database level if provided
        if search_query:
            search_term = f'%{search_query}%'
            query = query.filter(
                db.or_(
                    Course.name.ilike(search_term),
                    Course.description.ilike(search_term)
                )
            )
        
        enrollments = query.order_by(CourseStudent.assigned_at.desc()).all()
        
        courses_data = []
        for enrollment in enrollments:
            course = enrollment.course
            if course:
                # Get tutors assigned to this course
                tutor_assignments = db.session.query(course_tutors).filter_by(course_id=course.id).all()
                tutors_data = []
                for assignment in tutor_assignments:
                    tutor = User.query.get(assignment.tutor_id)
                    if tutor:
                        tutors_data.append({
                            'id': tutor.id,
                            'full_name': tutor.full_name,
                            'email': tutor.email
                        })
                
                # Calculate progress for this course
                modules = CourseModule.query.filter_by(course_id=course.id).all()
                total_files = 0
                file_ids = []
                
                for module in modules:
                    files = ModuleFile.query.filter_by(module_id=module.id).all()
                    total_files += len(files)
                    file_ids.extend([f.id for f in files])
                
                # Get viewed files for this student
                viewed_count = 0
                if file_ids:
                    viewed_progress = StudentFileProgress.query.filter(
                        StudentFileProgress.student_id == current_user.id,
                        StudentFileProgress.file_id.in_(file_ids)
                    ).all()
                    viewed_count = len(viewed_progress)
                
                # Calculate percentage
                percentage = round((viewed_count / total_files * 100) if total_files > 0 else 0, 1)
                
                courses_data.append({
                    'id': course.id,
                    'name': course.name,
                    'description': course.description or '',
                    'enrolled_at': enrollment.assigned_at.isoformat() if enrollment.assigned_at else None,
                    'tutor_count': len(tutors_data),
                    'tutors': tutors_data,
                    'progress': {
                        'percentage': percentage,
                        'viewed_files': viewed_count,
                        'total_files': total_files
                    }
                })
        
        return jsonify({'success': True, 'courses': courses_data}), 200
    except Exception as e:
        from flask import current_app
        current_app.logger.exception("Error listing enrolled courses")
        return jsonify({'success': False, 'error': 'Failed to load courses'}), 500


@student_bp.route('/api/courses/<int:course_id>/request', methods=['POST'])
@login_required
def request_to_join_course(course_id):
    """API endpoint for student to request to join a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        course = Course.query.get_or_404(course_id)
        
        # Check if already enrolled
        existing_enrollment = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if existing_enrollment:
            return jsonify({'success': False, 'error': 'Already enrolled in this course'}), 400
        
        # Check if already has pending request
        existing_request = CourseRequest.query.filter_by(
            course_id=course_id,
            student_id=current_user.id,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'error': 'Request already pending'}), 400
        
        # Get tutors assigned to this course
        tutor_assignments = db.session.query(course_tutors).filter_by(course_id=course_id).all()
        
        if not tutor_assignments:
            return jsonify({'success': False, 'error': 'No tutors assigned to this course'}), 400
        
        # Create requests for all tutors (they can all see and respond)
        from datetime import datetime
        for assignment in tutor_assignments:
            # Check if request already exists for this tutor
            existing = CourseRequest.query.filter_by(
                course_id=course_id,
                student_id=current_user.id,
                tutor_id=assignment.tutor_id
            ).first()
            
            if not existing:
                request_obj = CourseRequest(
                    course_id=course_id,
                    student_id=current_user.id,
                    tutor_id=assignment.tutor_id,
                    status='pending'
                )
                db.session.add(request_obj)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Request sent to course tutors'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error creating course request for {course_id}")
        return jsonify({'success': False, 'error': 'Failed to send request'}), 500


@student_bp.route('/api/courses/<int:course_id>/modules')
@login_required
def get_course_modules(course_id):
    """API endpoint for students to view modules of an enrolled course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify student is enrolled
        enrollment = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'Not enrolled in this course'}), 403
        
        # Get course
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Get modules
        modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index, CourseModule.created_at).all()
        modules_data = []
        for module in modules:
            # Get file count
            file_count = ModuleFile.query.filter_by(module_id=module.id).count()
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'description': module.description or '',
                'order_index': module.order_index,
                'created_at': module.created_at.isoformat() if module.created_at else None,
                'file_count': file_count
            })
        
        return jsonify({
            'success': True,
            'course': {
                'id': course.id,
                'name': course.name,
                'description': course.description or ''
            },
            'modules': modules_data
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting modules for course {course_id}")
        return jsonify({'success': False, 'error': 'Failed to load modules'}), 500


@student_bp.route('/api/modules/<int:module_id>/files')
@login_required
def get_module_files(module_id):
    """API endpoint for students to view files in a module."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get module
        module = CourseModule.query.get(module_id)
        if not module:
            return jsonify({'success': False, 'error': 'Module not found'}), 404
        
        # Verify student is enrolled in the course
        enrollment = CourseStudent.query.filter_by(
            course_id=module.course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'Not enrolled in this course'}), 403
        
        # Get files
        files = ModuleFile.query.filter_by(module_id=module_id).order_by(ModuleFile.uploaded_at).all()
        files_data = []
        for file_obj in files:
            files_data.append({
                'id': file_obj.id,
                'file_name': file_obj.file_name,
                'file_path': file_obj.file_path,
                'file_type': file_obj.file_type,
                'file_size': file_obj.file_size,
                'mime_type': file_obj.mime_type,
                'uploaded_at': file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None,
                'url': get_file_url(file_obj.file_path)
            })
        
        return jsonify({
            'success': True,
            'module': {
                'id': module.id,
                'name': module.name,
                'description': module.description or ''
            },
            'files': files_data
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting files for module {module_id}")
        return jsonify({'success': False, 'error': 'Failed to load files'}), 500


@student_bp.route('/api/courses/<int:course_id>/view', methods=['GET'])
@login_required
def get_course_view(course_id):
    """API endpoint to get course view HTML content for student dashboard."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify student is enrolled in this course
        enrollment = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'Course not found or not enrolled'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Get tutors assigned to this course
        tutor_assignments = db.session.query(course_tutors).filter_by(course_id=course_id).all()
        tutors_data = []
        for assignment in tutor_assignments:
            tutor = User.query.get(assignment.tutor_id)
            if tutor:
                tutors_data.append({
                    'id': tutor.id,
                    'full_name': tutor.full_name,
                    'email': tutor.email
                })
        
        # Get modules for this course
        modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index, CourseModule.created_at).all()
        modules_data = []
        for module in modules:
            # Get files for this module
            module_files = ModuleFile.query.filter_by(module_id=module.id).order_by(ModuleFile.uploaded_at).all()
            files_data = []
            for file_obj in module_files:
                files_data.append({
                    'id': file_obj.id,
                    'file_name': file_obj.file_name,
                    'file_path': file_obj.file_path,
                    'file_type': file_obj.file_type,
                    'file_size': file_obj.file_size,
                    'mime_type': file_obj.mime_type,
                    'uploaded_at': file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None,
                    'url': get_file_url(file_obj.file_path)
                })
            
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'description': module.description or '',
                'order_index': module.order_index,
                'created_at': module.created_at.isoformat() if module.created_at else None,
                'files': files_data,
                'file_count': len(files_data)
            })
        
        # Render course view template
        html = render_template('student/course_view.html', 
                              course=course, 
                              tutors=tutors_data,
                              modules=modules_data,
                              course_id=course_id)
        
        return jsonify({'success': True, 'html': html}), 200
        
    except Exception as e:
        from flask import current_app
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.exception(f"Error getting course view for {course_id}")
        current_app.logger.error(f"Full traceback: {error_trace}")
        return jsonify({
            'success': False, 
            'error': f'Failed to load course: {str(e)}',
            'details': str(e) if current_app.debug else None
        }), 500


@student_bp.route('/api/progress/file/<int:file_id>/track', methods=['POST'])
@login_required
def track_file_view(file_id):
    """API endpoint to track when a student views a file."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get the file and verify it exists
        file_obj = ModuleFile.query.get(file_id)
        if not file_obj:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Get the course_id from the module
        course_id = file_obj.module.course_id
        
        # Verify student is enrolled in the course
        enrollment = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'You are not enrolled in this course'}), 403
        
        # Check if progress already exists
        progress = StudentFileProgress.query.filter_by(
            student_id=current_user.id,
            file_id=file_id
        ).first()
        
        from datetime import datetime
        if progress:
            # Update existing progress
            progress.last_viewed_at = datetime.utcnow()
            progress.view_count += 1
        else:
            # Create new progress record
            progress = StudentFileProgress(
                student_id=current_user.id,
                file_id=file_id,
                course_id=course_id,
                first_viewed_at=datetime.utcnow(),
                last_viewed_at=datetime.utcnow(),
                view_count=1
            )
            db.session.add(progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated',
            'view_count': progress.view_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error tracking file view for file {file_id}")
        return jsonify({'success': False, 'error': 'Failed to track progress'}), 500


@student_bp.route('/api/courses/<int:course_id>/progress', methods=['GET'])
@login_required
def get_course_progress(course_id):
    """API endpoint to get student's progress for a specific course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify student is enrolled
        enrollment = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'You are not enrolled in this course'}), 403
        
        # Get all files in the course (across all modules)
        modules = CourseModule.query.filter_by(course_id=course_id).all()
        total_files = 0
        file_ids = []
        
        for module in modules:
            files = ModuleFile.query.filter_by(module_id=module.id).all()
            total_files += len(files)
            file_ids.extend([f.id for f in files])
        
        # Get viewed files
        viewed_progress = StudentFileProgress.query.filter(
            StudentFileProgress.student_id == current_user.id,
            StudentFileProgress.file_id.in_(file_ids)
        ).all()
        
        viewed_count = len(viewed_progress)
        viewed_file_ids = {p.file_id for p in viewed_progress}
        
        # Calculate percentage
        percentage = round((viewed_count / total_files * 100) if total_files > 0 else 0, 2)
        
        # Get detailed progress per module
        modules_progress = []
        for module in modules:
            module_files = ModuleFile.query.filter_by(module_id=module.id).all()
            module_total = len(module_files)
            module_viewed = sum(1 for f in module_files if f.id in viewed_file_ids)
            module_percentage = round((module_viewed / module_total * 100) if module_total > 0 else 0, 2)
            
            modules_progress.append({
                'module_id': module.id,
                'module_name': module.name,
                'total_files': module_total,
                'viewed_files': module_viewed,
                'percentage': module_percentage
            })
        
        return jsonify({
            'success': True,
            'progress': {
                'total_files': total_files,
                'viewed_files': viewed_count,
                'percentage': percentage,
                'modules': modules_progress
            }
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting progress for course {course_id}")
        return jsonify({'success': False, 'error': 'Failed to get progress'}), 500