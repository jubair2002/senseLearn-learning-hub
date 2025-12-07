from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from src import db
from src.student import student_bp

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