"""
Tutor routes for quiz management.

Tutors can:
- Create quizzes for courses/modules
- Add questions to quizzes
- View quiz results and student attempts
"""
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from src import db
from src.quiz import quiz_bp
from src.quiz.models import Quiz, Question, QuestionOption, QuizAttempt, Answer
from src.auth.models import Course, CourseModule, course_tutors
from decimal import Decimal, InvalidOperation


@quiz_bp.route('/api/courses/<int:course_id>/quizzes', methods=['GET'])
@login_required
def list_quizzes(course_id):
    """
    List all quizzes for a course.
    Only tutors assigned to the course can view quizzes.
    """
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
        
        # Get course
        course = Course.query.get_or_404(course_id)
        
        # Get all quizzes for this course - use explicit query to avoid caching
        quizzes = db.session.query(Quiz).filter_by(course_id=course_id).order_by(Quiz.order_index, Quiz.created_at).all()
        
        print(f"Found {len(quizzes)} quizzes for course {course_id}")
        for quiz in quizzes:
            print(f"  Quiz ID={quiz.id}, Title={quiz.title}, Module ID={quiz.module_id}")
        
        quizzes_data = []
        for quiz in quizzes:
            quiz_data = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'module_id': quiz.module_id,
                'module_name': quiz.module.name if quiz.module else None,
                'time_limit_minutes': quiz.time_limit_minutes,
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
                'max_attempts': quiz.max_attempts,
                'is_active': quiz.is_active,
                'order_index': quiz.order_index,
                'question_count': quiz.get_question_count(),
                'total_points': float(quiz.get_total_points()),
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


@quiz_bp.route('/api/courses/<int:course_id>/quizzes', methods=['POST'])
@login_required
def create_quiz(course_id):
    """
    Create a new quiz for a course or module.
    
    Request body:
    {
        "title": "Quiz Title",
        "description": "Optional description",
        "instructions": "Instructions for students",
        "module_id": 123,  // Optional: if provided, quiz is attached to module
        "time_limit_minutes": 30,  // Optional
        "passing_score": 60.0,  // Optional, default 60
        "max_attempts": 1,  // Optional, default 1
        "order_index": 0  // Optional, for ordering
    }
    """
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
        
        # Verify course exists
        course = Course.query.get_or_404(course_id)
        
        data = request.get_json() or {}
        
        # Validate required fields
        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'success': False, 'error': 'Quiz title is required'}), 400
        
        # Validate module_id if provided
        module_id = data.get('module_id')
        if module_id:
            module = CourseModule.query.filter_by(id=module_id, course_id=course_id).first()
            if not module:
                return jsonify({'success': False, 'error': 'Module not found or not in this course'}), 404
        
        # Create quiz
        quiz = Quiz(
            course_id=course_id,
            module_id=module_id,  # This can be None if not provided
            title=title,
            description=(data.get('description') or '').strip() or None,
            instructions=(data.get('instructions') or '').strip() or None,
            time_limit_minutes=data.get('time_limit_minutes'),
            passing_score=Decimal(str(data.get('passing_score', 60.0))) if data.get('passing_score') else Decimal('60.0'),
            max_attempts=data.get('max_attempts', 1),
            order_index=data.get('order_index', 0),
            created_by=current_user.id
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        # Verify the quiz was saved correctly
        saved_quiz = Quiz.query.get(quiz.id)
        if saved_quiz:
            print(f"Quiz saved: ID={saved_quiz.id}, Title={saved_quiz.title}, Module ID={saved_quiz.module_id}, Course ID={saved_quiz.course_id}")
        
        return jsonify({
            'success': True,
            'message': 'Quiz created successfully',
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'module_id': quiz.module_id,
                'time_limit_minutes': quiz.time_limit_minutes,
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
                'max_attempts': quiz.max_attempts,
                'order_index': quiz.order_index,
                'created_at': quiz.created_at.isoformat() if quiz.created_at else None,
            }
        }), 201
        
    except (ValueError, InvalidOperation) as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Invalid numeric value: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>', methods=['GET'])
@login_required
def get_quiz(quiz_id):
    """
    Get quiz details including all questions.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Quiz not found or not authorized'}), 404
        
        # Get questions with options
        questions_data = []
        for question in quiz.questions.order_by(Question.order_index).all():
            question_data = {
                'id': question.id,
                'question_type': question.question_type,
                'question_text': question.question_text,
                'points': float(question.points),
                'order_index': question.order_index,
                'correct_answer': question.get_correct_answer(),
            }
            
            # Add options for multiple choice
            if question.question_type == 'multiple_choice':
                question_data['options'] = [
                    {
                        'id': opt.id,
                        'option_text': opt.option_text,
                        'is_correct': opt.is_correct,
                        'order_index': opt.order_index
                    }
                    for opt in question.options.order_by(QuestionOption.order_index).all()
                ]
            
            questions_data.append(question_data)
        
        return jsonify({
            'success': True,
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'instructions': quiz.instructions,
                'course_id': quiz.course_id,
                'module_id': quiz.module_id,
                'module_name': quiz.module.name if quiz.module else None,
                'time_limit_minutes': quiz.time_limit_minutes,
                'passing_score': float(quiz.passing_score) if quiz.passing_score else None,
                'max_attempts': quiz.max_attempts,
                'is_active': quiz.is_active,
                'order_index': quiz.order_index,
                'question_count': quiz.get_question_count(),
                'total_points': float(quiz.get_total_points()),
                'created_at': quiz.created_at.isoformat() if quiz.created_at else None,
                'questions': questions_data
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>', methods=['PUT', 'PATCH'])
@login_required
def update_quiz(quiz_id):
    """
    Update quiz details.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Quiz not found or not authorized'}), 404
        
        data = request.get_json() or {}
        
        # Update fields if provided
        if 'title' in data:
            quiz.title = (data.get('title') or '').strip()
        if 'description' in data:
            quiz.description = (data.get('description') or '').strip() or None
        if 'instructions' in data:
            quiz.instructions = (data.get('instructions') or '').strip() or None
        if 'time_limit_minutes' in data:
            quiz.time_limit_minutes = data['time_limit_minutes']
        if 'passing_score' in data:
            quiz.passing_score = Decimal(str(data['passing_score']))
        if 'max_attempts' in data:
            quiz.max_attempts = data['max_attempts'] if data['max_attempts'] is not None and data['max_attempts'] != '' else None
        if 'is_active' in data:
            quiz.is_active = bool(data['is_active'])
        if 'order_index' in data:
            quiz.order_index = data['order_index']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz updated successfully',
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'is_active': quiz.is_active
            }
        }), 200
        
    except (ValueError, InvalidOperation) as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Invalid numeric value: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>', methods=['DELETE'])
@login_required
def delete_quiz(quiz_id):
    """
    Delete a quiz.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Quiz not found or not authorized'}), 404
        
        db.session.delete(quiz)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Quiz deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>/questions', methods=['POST'])
@login_required
def add_question(quiz_id):
    """
    Add a question to a quiz.
    
    Request body for multiple_choice:
    {
        "question_type": "multiple_choice",
        "question_text": "What is 2+2?",
        "points": 1.0,
        "options": [
            {"option_text": "3", "is_correct": false},
            {"option_text": "4", "is_correct": true},
            {"option_text": "5", "is_correct": false}
        ],
        "order_index": 0
    }
    
    Request body for short_answer:
    {
        "question_type": "short_answer",
        "question_text": "What is the capital of France?",
        "points": 2.0,
        "correct_answer": "Paris",
        "order_index": 1
    }
    
    Request body for true_false:
    {
        "question_type": "true_false",
        "question_text": "Python is a programming language.",
        "points": 1.0,
        "correct_answer": "true",
        "order_index": 2
    }
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Quiz not found or not authorized'}), 404
        
        data = request.get_json() or {}
        
        # Validate required fields
        question_type = (data.get('question_type') or '').strip()
        if question_type not in ['multiple_choice', 'short_answer', 'true_false']:
            return jsonify({
                'success': False,
                'error': 'Invalid question_type. Must be: multiple_choice, short_answer, or true_false'
            }), 400
        
        question_text = (data.get('question_text') or '').strip()
        if not question_text:
            return jsonify({'success': False, 'error': 'question_text is required'}), 400
        
        points = Decimal(str(data.get('points', 1.0)))
        if points <= 0:
            return jsonify({'success': False, 'error': 'points must be greater than 0'}), 400
        
        # Create question
        question = Question(
            quiz_id=quiz_id,
            question_type=question_type,
            question_text=question_text,
            points=points,
            order_index=data.get('order_index', 0),
            correct_answer=(data.get('correct_answer') or '').strip() if question_type in ['short_answer', 'true_false'] else None
        )
        
        db.session.add(question)
        db.session.flush()  # Get question.id
        
        # Add options for multiple choice
        if question_type == 'multiple_choice':
            options = data.get('options', [])
            if not options or len(options) < 2:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'multiple_choice questions require at least 2 options'}), 400
            
            # Check that exactly one option is correct
            correct_count = sum(1 for opt in options if opt.get('is_correct', False))
            if correct_count != 1:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'multiple_choice questions must have exactly one correct option'}), 400
            
            for idx, opt_data in enumerate(options):
                option = QuestionOption(
                    question_id=question.id,
                    option_text=(opt_data.get('option_text') or '').strip(),
                    is_correct=bool(opt_data.get('is_correct', False)),
                    order_index=opt_data.get('order_index', idx)
                )
                db.session.add(option)
        
        db.session.commit()
        
        # Return question with options
        question_data = {
            'id': question.id,
            'question_type': question.question_type,
            'question_text': question.question_text,
            'points': float(question.points),
            'order_index': question.order_index,
            'correct_answer': question.get_correct_answer(),
        }
        
        if question_type == 'multiple_choice':
            question_data['options'] = [
                {
                    'id': opt.id,
                    'option_text': opt.option_text,
                    'is_correct': opt.is_correct,
                    'order_index': opt.order_index
                }
                for opt in question.options.order_by(QuestionOption.order_index).all()
            ]
        
        return jsonify({
            'success': True,
            'message': 'Question added successfully',
            'question': question_data
        }), 201
        
    except (ValueError, InvalidOperation) as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Invalid numeric value: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/questions/<int:question_id>', methods=['GET'])
@login_required
def get_question(question_id):
    """
    Get a single question with its options.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        
        # Get quiz to verify authorization
        quiz = Quiz.query.get(question.quiz_id)
        if not quiz:
            return jsonify({'success': False, 'error': 'Quiz not found for this question'}), 404
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Question not found or not authorized'}), 404
        
        question_data = {
            'id': question.id,
            'quiz_id': question.quiz_id,
            'question_type': question.question_type,
            'question_text': question.question_text,
            'points': float(question.points),
            'order_index': question.order_index,
            'correct_answer': question.correct_answer,
        }
        
        # Add options for multiple choice
        if question.question_type == 'multiple_choice':
            question_data['options'] = [
                {
                    'id': opt.id,
                    'option_text': opt.option_text,
                    'is_correct': opt.is_correct,
                    'order_index': opt.order_index
                }
                for opt in question.options.order_by(QuestionOption.order_index).all()
            ]
        
        return jsonify({
            'success': True,
            'question': question_data
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Error in get_question: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/questions/<int:question_id>', methods=['PUT', 'PATCH'])
@login_required
def update_question(question_id):
    """
    Update a question.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        
        # Get quiz to verify authorization
        quiz = Quiz.query.get(question.quiz_id)
        if not quiz:
            return jsonify({'success': False, 'error': 'Quiz not found for this question'}), 404
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Question not found or not authorized'}), 404
        
        data = request.get_json() or {}
        
        # Update fields
        if 'question_text' in data:
            question.question_text = (data.get('question_text') or '').strip()
        if 'points' in data:
            question.points = Decimal(str(data['points']))
        if 'order_index' in data:
            question.order_index = data['order_index']
        if 'correct_answer' in data and question.question_type in ['short_answer', 'true_false']:
            question.correct_answer = (data.get('correct_answer') or '').strip()
        
        # Update options for multiple choice
        if question.question_type == 'multiple_choice' and 'options' in data:
            # Delete existing options
            question.options.delete()
            db.session.flush()
            
            # Add new options
            options = data['options']
            if not options or len(options) < 2:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'multiple_choice questions require at least 2 options'}), 400
            
            correct_count = sum(1 for opt in options if opt.get('is_correct', False))
            if correct_count != 1:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'multiple_choice questions must have exactly one correct option'}), 400
            
            for idx, opt_data in enumerate(options):
                option = QuestionOption(
                    question_id=question.id,
                    option_text=(opt_data.get('option_text') or '').strip(),
                    is_correct=bool(opt_data.get('is_correct', False)),
                    order_index=opt_data.get('order_index', idx)
                )
                db.session.add(option)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question updated successfully'
        }), 200
        
    except (ValueError, InvalidOperation) as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Invalid numeric value: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/questions/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    """
    Delete a question.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        question = Question.query.get_or_404(question_id)
        quiz = question.quiz
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Question not found or not authorized'}), 404
        
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Question deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@quiz_bp.route('/api/quizzes/<int:quiz_id>/attempts', methods=['GET'])
@login_required
def get_quiz_attempts(quiz_id):
    """
    Get all student attempts for a quiz.
    Tutors can see all attempts with scores and answers.
    """
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Verify tutor is assigned to the course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=quiz.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Quiz not found or not authorized'}), 404
        
        # Get all attempts
        attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).order_by(QuizAttempt.submitted_at.desc()).all()
        
        attempts_data = []
        for attempt in attempts:
            attempt_data = {
                'id': attempt.id,
                'student_id': attempt.student_id,
                'student_name': attempt.student.full_name if attempt.student else 'Unknown',
                'student_email': attempt.student.email if attempt.student else 'Unknown',
                'started_at': attempt.started_at.isoformat() if attempt.started_at else None,
                'submitted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                'is_completed': attempt.is_completed,
                'score': float(attempt.score) if attempt.score else None,
                'total_points': float(attempt.total_points) if attempt.total_points else None,
                'max_points': float(attempt.max_points) if attempt.max_points else None,
                'is_passing': attempt.is_passing() if attempt.is_completed else None,
            }
            
            # Add answers if completed
            if attempt.is_completed:
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
                attempt_data['answers'] = answers_data
            
            attempts_data.append(attempt_data)
        
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'quiz_title': quiz.title,
            'attempts': attempts_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

