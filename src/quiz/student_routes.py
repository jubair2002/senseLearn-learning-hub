"""
Student routes for quiz functionality.

Students can:
- View quizzes available in their enrolled courses
- Start quiz attempts
- Submit quiz answers
"""
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from src import db
from src.quiz import quiz_bp
from src.quiz.models import Quiz, Question, QuestionOption, QuizAttempt, Answer
from src.auth.models import Course, CourseStudent, CourseModule
from decimal import Decimal


@quiz_bp.route('/api/courses/<int:course_id>/quizzes', methods=['GET'])
@login_required
def list_course_quizzes_student(course_id):
    """
    List all quizzes available to a student in a course.
    Only shows quizzes for courses the student is enrolled in.
    """
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
        
        # Get course
        course = Course.query.get_or_404(course_id)
        
        # Get all active quizzes for this course
        quizzes = Quiz.query.filter_by(
            course_id=course_id,
            is_active=True
        ).order_by(Quiz.order_index, Quiz.created_at).all()
        
        quizzes_data = []
        for quiz in quizzes:
            # Check if student has any attempts
            attempts = QuizAttempt.query.filter_by(
                quiz_id=quiz.id,
                student_id=current_user.id
            ).all()
            
            completed_attempts = [a for a in attempts if a.is_completed]
            total_attempts = len(attempts)
            completed_count = len(completed_attempts)
            
            # Check if student can take the quiz - use current max_attempts (allows resubmission if limit increased)
            can_take = True
            if quiz.max_attempts and completed_count >= quiz.max_attempts:
                can_take = False
            
            # Get latest attempt score (only latest counts)
            latest_score = None
            if completed_attempts:
                # Get the most recent completed attempt
                latest_attempt = max(completed_attempts, key=lambda a: a.submitted_at if a.submitted_at else a.started_at)
                if latest_attempt and latest_attempt.score is not None:
                    try:
                        latest_score = float(latest_attempt.score)
                    except (ValueError, TypeError):
                        latest_score = None
            
            quiz_data = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'module_id': quiz.module_id,
                'module_name': quiz.module.name if quiz.module else None,
                'time_limit_minutes': quiz.time_limit_minutes,
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
                'max_attempts': quiz.max_attempts,
                'question_count': quiz.get_question_count(),
                'total_points': float(quiz.get_total_points()),
                'can_take': can_take,
                'attempts_count': total_attempts,
                'completed_attempts': completed_count,
                'latest_score': latest_score,  # Only latest attempt counts
                'created_at': quiz.created_at.isoformat() if quiz.created_at else None,
            }
            quizzes_data.append(quiz_data)
        
        return jsonify({
            'success': True,
            'quizzes': quizzes_data,
            'course_id': course_id,
            'course_name': course.name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz_attempt(quiz_id):
    """
    Start a new quiz attempt for a student.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Verify student is enrolled in the course
        enrollment = CourseStudent.query.filter_by(
            course_id=quiz.course_id,
            student_id=current_user.id,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'success': False, 'error': 'Quiz not found or not enrolled in course'}), 404
        
        # Check if quiz is active
        if not quiz.is_active:
            return jsonify({'success': False, 'error': 'This quiz is not available'}), 400
        
        # Check attempt limit - use current max_attempts value (allows resubmission if limit increased)
        if quiz.max_attempts:
            completed_attempts = QuizAttempt.query.filter_by(
                quiz_id=quiz_id,
                student_id=current_user.id,
                is_completed=True
            ).count()
            
            if completed_attempts >= quiz.max_attempts:
                return jsonify({
                    'success': False,
                    'error': f'Maximum attempts ({quiz.max_attempts}) reached for this quiz'
                }), 400
        
        # Check if there's an incomplete attempt
        incomplete_attempt = QuizAttempt.query.filter_by(
            quiz_id=quiz_id,
            student_id=current_user.id,
            is_completed=False
        ).first()
        
        if incomplete_attempt:
            # Return existing incomplete attempt
            return jsonify({
                'success': True,
                'attempt': {
                    'id': incomplete_attempt.id,
                    'quiz_id': incomplete_attempt.quiz_id,
                    'started_at': incomplete_attempt.started_at.isoformat(),
                    'time_limit_minutes': quiz.time_limit_minutes,
                },
                'message': 'Resuming existing attempt'
            }), 200
        
        # Create new attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=current_user.id,
            started_at=datetime.utcnow(),
            is_completed=False
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'attempt': {
                'id': attempt.id,
                'quiz_id': attempt.quiz_id,
                'started_at': attempt.started_at.isoformat(),
                'time_limit_minutes': quiz.time_limit_minutes,
            },
            'message': 'Quiz attempt started'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error in start_quiz_attempt: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/attempts/<int:attempt_id>/questions', methods=['GET'])
@login_required
def get_quiz_questions(attempt_id):
    """
    Get all questions for a quiz attempt.
    Only returns questions, not answers (to prevent cheating).
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        
        # Verify the attempt belongs to the current student
        if attempt.student_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Verify attempt is not completed
        if attempt.is_completed:
            return jsonify({'success': False, 'error': 'This quiz attempt is already completed'}), 400
        
        quiz = attempt.quiz
        
        # Get all questions with options (but not correct answers)
        questions_data = []
        for question in quiz.questions.order_by(Question.order_index).all():
            question_data = {
                'id': question.id,
                'question_type': question.question_type,
                'question_text': question.question_text,
                'points': float(question.points),
                'order_index': question.order_index,
            }
            
            # Add options for multiple choice (without is_correct flag)
            if question.question_type == 'multiple_choice':
                question_data['options'] = [
                    {
                        'id': opt.id,
                        'option_text': opt.option_text,
                        'order_index': opt.order_index
                    }
                    for opt in question.options.order_by(QuestionOption.order_index).all()
                ]
            
            questions_data.append(question_data)
        
        # Get existing answers if any
        existing_answers = {}
        for answer in attempt.answers.all():
            existing_answers[answer.question_id] = {
                'answer_text': answer.answer_text,
                'option_id': answer.option_id,
            }
        
        return jsonify({
            'success': True,
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'instructions': quiz.instructions,
                'time_limit_minutes': quiz.time_limit_minutes,
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
            },
            'attempt': {
                'id': attempt.id,
                'started_at': attempt.started_at.isoformat(),
            },
            'questions': questions_data,
            'existing_answers': existing_answers
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Error in get_quiz_questions: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/attempts/<int:attempt_id>/answer', methods=['POST'])
@login_required
def save_answer(attempt_id):
    """
    Save or update an answer for a question in a quiz attempt.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        
        # Verify the attempt belongs to the current student
        if attempt.student_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Verify attempt is not completed
        if attempt.is_completed:
            return jsonify({'success': False, 'error': 'This quiz attempt is already completed'}), 400
        
        data = request.get_json() or {}
        question_id = data.get('question_id')
        answer_text = data.get('answer_text')
        option_id = data.get('option_id')
        
        if not question_id:
            return jsonify({'success': False, 'error': 'question_id is required'}), 400
        
        # Verify question belongs to the quiz
        question = Question.query.get(question_id)
        if not question or question.quiz_id != attempt.quiz_id:
            return jsonify({'success': False, 'error': 'Invalid question'}), 400
        
        # Check if answer already exists
        existing_answer = Answer.query.filter_by(
            attempt_id=attempt_id,
            question_id=question_id
        ).first()
        
        if existing_answer:
            # Update existing answer
            if question.question_type == 'multiple_choice':
                existing_answer.option_id = option_id
                existing_answer.answer_text = None
            else:
                existing_answer.answer_text = (answer_text or '').strip()
                existing_answer.option_id = None
            
            existing_answer.answered_at = datetime.utcnow()
        else:
            # Create new answer
            answer = Answer(
                attempt_id=attempt_id,
                question_id=question_id,
                answer_text=(answer_text or '').strip() if question.question_type != 'multiple_choice' else None,
                option_id=option_id if question.question_type == 'multiple_choice' else None,
            )
            db.session.add(answer)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Answer saved'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error in save_answer: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/attempts/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_quiz_attempt(attempt_id):
    """
    Submit a completed quiz attempt.
    This will auto-grade all answers and calculate the score.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        
        # Verify the attempt belongs to the current student
        if attempt.student_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Verify attempt is not already completed
        if attempt.is_completed:
            return jsonify({'success': False, 'error': 'This quiz attempt is already completed'}), 400
        
        quiz = attempt.quiz
        
        # Get all answers and grade them
        answers = attempt.answers.all()
        
        # Check and grade each answer
        for answer in answers:
            answer.check_and_update()
        
        # Mark attempt as completed
        attempt.is_completed = True
        attempt.submitted_at = datetime.utcnow()
        
        # Calculate score
        attempt.calculate_score()
        
        db.session.commit()
        
        # Get detailed results
        answers_data = []
        for answer in attempt.answers.all():
            answer_data = {
                'question_id': answer.question_id,
                'question_text': answer.question.question_text,
                'question_type': answer.question.question_type,
                'answer_text': answer.answer_text,
                'option_id': answer.option_id,
                'option_text': answer.option.option_text if answer.option else None,
                'is_correct': answer.is_correct,
                'points_earned': float(answer.points_earned) if answer.points_earned else 0,
                'correct_answer': answer.question.get_correct_answer(),
            }
            answers_data.append(answer_data)
        
        return jsonify({
            'success': True,
            'attempt': {
                'id': attempt.id,
                'score': float(attempt.score) if attempt.score else 0,
                'total_points': float(attempt.total_points) if attempt.total_points else 0,
                'max_points': float(attempt.max_points) if attempt.max_points else 0,
                'is_passing': attempt.is_passing(),
                'submitted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            },
            'quiz': {
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
            },
            'answers': answers_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error in submit_quiz_attempt: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>/attempts', methods=['GET'])
def list_student_attempts(quiz_id):
    """
    List all attempts by the current user for a quiz.
    Any logged-in user can view their own attempts.
    """
    # Manual authentication check (more flexible than @login_required)
    if not current_user.is_authenticated:
        current_app.logger.warning(f"Unauthenticated access attempt to list_student_attempts: quiz_id={quiz_id}")
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        # Log entry point
        current_app.logger.info(f"list_student_attempts called: quiz_id={quiz_id}, user_id={current_user.id}, user_authenticated={current_user.is_authenticated}")
        
        # Debug logging
        current_app.logger.info(f"list_student_attempts: quiz_id={quiz_id}, user_id={current_user.id}, user_type={getattr(current_user, 'user_type', 'N/A')}")
        
        # Get quiz - use get() instead of get_or_404 to handle 404 ourselves
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            current_app.logger.warning(f"Quiz not found: quiz_id={quiz_id}")
            return jsonify({'success': False, 'error': 'Quiz not found'}), 404
        
        # Get all attempts by this user for this quiz
        attempts = QuizAttempt.query.filter_by(
            quiz_id=quiz_id,
            student_id=current_user.id
        ).order_by(QuizAttempt.submitted_at.desc(), QuizAttempt.started_at.desc()).all()
        
        current_app.logger.debug(f"list_student_attempts: found {len(attempts)} attempts for user {current_user.id} in quiz {quiz_id}")
        
        # Process attempts data - only latest completed attempt counts
        attempts_data = []
        latest_completed = None
        for attempt in attempts:
            attempt_data = {
                'id': attempt.id,
                'started_at': attempt.started_at.isoformat() if attempt.started_at else None,
                'submitted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                'is_completed': attempt.is_completed,
                'score': float(attempt.score) if attempt.score else None,
                'total_points': float(attempt.total_points) if attempt.total_points else None,
                'max_points': float(attempt.max_points) if attempt.max_points else None,
                'is_passing': attempt.is_passing() if attempt.is_completed else None,
                'is_latest': False,  # Will be set below
            }
            
            # Mark the latest completed attempt
            if attempt.is_completed and latest_completed is None:
                latest_completed = attempt.id
                attempt_data['is_latest'] = True
            
            attempts_data.append(attempt_data)
        
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'quiz_title': quiz.title,
            'max_attempts': quiz.max_attempts,
            'attempts': attempts_data,
            'latest_attempt_id': latest_completed
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Error in list_student_attempts: {str(e)}")
        current_app.logger.error(error_trace)
        return jsonify({
            'success': False, 
            'error': f'Failed to load quiz attempts: {str(e)}'
        }), 500

