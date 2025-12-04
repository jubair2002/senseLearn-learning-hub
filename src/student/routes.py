from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from src.student import student_bp
from src import db

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard page."""
    # Check if user is actually a student
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        flash('This page is only for students.', 'error')
        return redirect('/')
    
    return render_template('student/dashboard.html', user=current_user)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Student profile page."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        flash('This page is only for students.', 'error')
        return redirect('/')
    
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
    """API endpoint for student dashboard stats."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock data - replace with real queries
    stats = {
        'total_sessions': 12,
        'completed_sessions': 10,
        'upcoming_sessions': 2,
        'hours_learned': 36,
        'tutors_count': 3,
        'avg_rating': 4.5
    }
    return jsonify(stats)