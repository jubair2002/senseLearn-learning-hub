from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from src import db
from src.student import student_bp

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard page."""
    # Check if user is actually a student
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        flash('This page is only for students.', 'error')
        return redirect(url_for('index'))
    
    return render_template('student/dashboard.html', user=current_user)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Student profile page."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        flash('This page is only for students.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Update profile
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip() or None
        disability_type = request.form.get('disability_type', '').strip()
        
        if not full_name or not disability_type:
            flash('Full name and disability type are required.', 'error')
        else:
            current_user.full_name = full_name
            current_user.phone_number = phone_number
            current_user.disability_type = disability_type
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
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