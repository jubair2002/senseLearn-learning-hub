from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from decimal import Decimal
from src import db
from src.tutor import tutor_bp

@tutor_bp.route('/dashboard')
@login_required
def dashboard():
    """Tutor dashboard page."""
    # Check if user is actually a tutor
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        flash('This page is only for tutors.', 'error')
        return redirect(url_for('index'))
    
    return render_template('tutor/dashboard.html', user=current_user)

@tutor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Tutor profile page."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        flash('This page is only for tutors.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Update profile
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
            for error in errors:
                flash(error, 'error')
        else:
            current_user.full_name = full_name
            current_user.phone_number = phone_number
            current_user.qualifications = qualifications
            current_user.experience_years = int(experience_years)
            current_user.subjects = subjects
            current_user.hourly_rate = Decimal(hourly_rate)
            current_user.bio = bio
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
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

@tutor_bp.route('/api/stats')
@login_required
def get_stats():
    """API endpoint for tutor dashboard stats."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Mock data - replace with real queries
    stats = {
        'total_students': 8,
        'total_sessions': 45,
        'upcoming_sessions': 6,
        'total_earnings': 1250.50,
        'avg_rating': 4.8,
        'completion_rate': 92
    }
    return jsonify(stats)