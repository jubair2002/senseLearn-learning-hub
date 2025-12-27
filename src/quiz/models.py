"""
Database models for quiz functionality.

Supports multiple question types:
- multiple_choice: Multiple choice questions with options
- short_answer: Short text answer questions
- true_false: True/False questions
"""
from datetime import datetime
from flask_login import UserMixin
from src import db


class Quiz(db.Model):
    """
    Model for quizzes within courses or modules.
    
    A quiz can be attached to:
    - A course (course_id set, module_id null)
    - A specific module (module_id set)
    """
    __tablename__ = "quizzes"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete='CASCADE'), nullable=False, index=True)
    module_id = db.Column(db.Integer, db.ForeignKey("course_modules.id", ondelete='CASCADE'), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=True)  # Instructions for students
    time_limit_minutes = db.Column(db.Integer, nullable=True)  # Optional time limit
    passing_score = db.Column(db.Numeric(5, 2), nullable=True, default=60.0)  # Passing percentage
    max_attempts = db.Column(db.Integer, nullable=True, default=1)  # Max attempts allowed
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)  # For ordering quizzes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='SET NULL'), nullable=True)
    
    # Relationships
    course = db.relationship("Course", backref="quizzes")
    module = db.relationship("CourseModule", backref="quizzes")
    creator = db.relationship("User", foreign_keys=[created_by])
    questions = db.relationship("Question", backref="quiz", lazy="dynamic", cascade="all, delete-orphan", order_by="Question.order_index")
    attempts = db.relationship("QuizAttempt", backref="quiz", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index('ix_quizzes_course_module', 'course_id', 'module_id'),
        db.Index('ix_quizzes_course_active', 'course_id', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<Quiz {self.id}: {self.title}>"
    
    def get_total_points(self) -> float:
        """Calculate total points for all questions."""
        return sum(q.points for q in self.questions)
    
    def get_question_count(self) -> int:
        """Get total number of questions."""
        return self.questions.count()


class Question(db.Model):
    """
    Model for quiz questions.
    
    Supports multiple question types:
    - multiple_choice: Has options, one correct answer
    - short_answer: Text answer, compared case-insensitively
    - true_false: Boolean answer
    """
    __tablename__ = "quiz_questions"
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete='CASCADE'), nullable=False, index=True)
    question_type = db.Column(db.String(50), nullable=False, index=True)  # multiple_choice, short_answer, true_false
    question_text = db.Column(db.Text, nullable=False)
    points = db.Column(db.Numeric(5, 2), nullable=False, default=1.0)  # Points for this question
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)  # For ordering questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # For short_answer: correct_answer stores the expected answer
    # For true_false: correct_answer stores "true" or "false"
    # For multiple_choice: correct_answer is not used, use QuestionOption.is_correct
    correct_answer = db.Column(db.Text, nullable=True)  # For short_answer and true_false
    
    # Relationships
    options = db.relationship("QuestionOption", backref="question", lazy="dynamic", cascade="all, delete-orphan", order_by="QuestionOption.order_index")
    answers = db.relationship("Answer", backref="question", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index('ix_quiz_questions_quiz_order', 'quiz_id', 'order_index'),
    )
    
    def __repr__(self) -> str:
        return f"<Question {self.id}: {self.question_type}>"
    
    def get_correct_answer(self) -> str:
        """Get the correct answer as a string for display."""
        if self.question_type == 'multiple_choice':
            correct_option = self.options.filter_by(is_correct=True).first()
            return correct_option.option_text if correct_option else ""
        elif self.question_type == 'true_false':
            return self.correct_answer or ""
        else:  # short_answer
            return self.correct_answer or ""
    
    def check_answer(self, student_answer: str) -> bool:
        """
        Check if student answer is correct.
        
        Args:
            student_answer: The answer provided by the student
            
        Returns:
            True if correct, False otherwise
        """
        if self.question_type == 'multiple_choice':
            # For multiple choice, check if student selected the correct option
            correct_option = self.options.filter_by(is_correct=True).first()
            if not correct_option:
                return False
            # Compare option IDs or text
            try:
                # If student_answer is an option ID
                option_id = int(student_answer)
                return option_id == correct_option.id
            except (ValueError, TypeError):
                # If student_answer is option text
                return student_answer.strip().lower() == correct_option.option_text.strip().lower()
        
        elif self.question_type == 'true_false':
            # Case-insensitive comparison
            correct = (self.correct_answer or "").strip().lower()
            student = (student_answer or "").strip().lower()
            return correct == student
        
        elif self.question_type == 'short_answer':
            # Case-insensitive comparison, trim whitespace
            correct = (self.correct_answer or "").strip().lower()
            student = (student_answer or "").strip().lower()
            return correct == student
        
        return False


class QuestionOption(db.Model):
    """
    Model for multiple choice question options.
    Only used for multiple_choice questions.
    """
    __tablename__ = "quiz_question_options"
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id", ondelete='CASCADE'), nullable=False, index=True)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False, index=True)
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)
    
    __table_args__ = (
        db.Index('ix_question_options_question_order', 'question_id', 'order_index'),
    )
    
    def __repr__(self) -> str:
        return f"<QuestionOption {self.id}: {self.option_text[:50]}>"


class QuizAttempt(db.Model):
    """
    Model for tracking student quiz attempts.
    """
    __tablename__ = "quiz_attempts"
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    score = db.Column(db.Numeric(5, 2), nullable=True)  # Percentage score
    total_points = db.Column(db.Numeric(5, 2), nullable=True)  # Total points earned
    max_points = db.Column(db.Numeric(5, 2), nullable=True)  # Maximum possible points
    
    # Relationships
    student = db.relationship("User", foreign_keys=[student_id], backref="quiz_attempts")
    answers = db.relationship("Answer", backref="attempt", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index('ix_quiz_attempts_quiz_student', 'quiz_id', 'student_id'),
        db.Index('ix_quiz_attempts_student_completed', 'student_id', 'is_completed'),
    )
    
    def __repr__(self) -> str:
        return f"<QuizAttempt {self.id}: Student {self.student_id}, Quiz {self.quiz_id}>"
    
    def calculate_score(self):
        """Calculate and update the score for this attempt."""
        if not self.is_completed:
            return
        
        total_points = 0
        max_points = 0
        
        for answer in self.answers:
            question = answer.question
            max_points += float(question.points)
            if answer.is_correct:
                total_points += float(question.points)
        
        self.total_points = total_points
        self.max_points = max_points
        
        if max_points > 0:
            self.score = (total_points / max_points) * 100
        else:
            self.score = 0
        
        db.session.commit()
    
    def is_passing(self) -> bool:
        """Check if the attempt meets the passing score."""
        if not self.quiz.passing_score or not self.score:
            return False
        return float(self.score) >= float(self.quiz.passing_score)


class Answer(db.Model):
    """
    Model for student answers to quiz questions.
    """
    __tablename__ = "quiz_answers"
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempts.id", ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id", ondelete='CASCADE'), nullable=False, index=True)
    answer_text = db.Column(db.Text, nullable=True)  # For short_answer and true_false
    option_id = db.Column(db.Integer, db.ForeignKey("quiz_question_options.id", ondelete='SET NULL'), nullable=True)  # For multiple_choice
    is_correct = db.Column(db.Boolean, nullable=True)  # Auto-calculated when submitted
    points_earned = db.Column(db.Numeric(5, 2), nullable=True)  # Points earned for this answer
    answered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    option = db.relationship("QuestionOption", foreign_keys=[option_id])
    
    __table_args__ = (
        db.UniqueConstraint('attempt_id', 'question_id', name='uq_attempt_question'),
        db.Index('ix_quiz_answers_attempt_question', 'attempt_id', 'question_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Answer {self.id}: Question {self.question_id}>"
    
    def check_and_update(self):
        """Check if answer is correct and update is_correct and points_earned."""
        question = self.question
        
        if question.question_type == 'multiple_choice':
            if self.option_id:
                correct_option = question.options.filter_by(is_correct=True).first()
                self.is_correct = (correct_option and self.option_id == correct_option.id)
            else:
                self.is_correct = False
        else:
            # For short_answer and true_false
            student_answer = self.answer_text or ""
            self.is_correct = question.check_answer(student_answer)
        
        # Update points earned
        if self.is_correct:
            self.points_earned = question.points
        else:
            self.points_earned = 0

