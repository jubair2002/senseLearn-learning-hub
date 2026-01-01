"""Add quiz system tables

Revision ID: b8dead1ae1ce
Revises: c18751849cce
Create Date: 2025-12-27 13:57:41.609908

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b8dead1ae1ce'
down_revision = 'c18751849cce'
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    tables = inspector.get_table_names()
    
    # Create quizzes table
    if 'quizzes' not in tables:
        op.create_table('quizzes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('module_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('instructions', sa.Text(), nullable=True),
            sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
            sa.Column('passing_score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('max_attempts', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_quizzes_course_id', 'quizzes', ['course_id'], unique=False)
        op.create_index('ix_quizzes_module_id', 'quizzes', ['module_id'], unique=False)
        op.create_index('ix_quizzes_is_active', 'quizzes', ['is_active'], unique=False)
        op.create_index('ix_quizzes_order_index', 'quizzes', ['order_index'], unique=False)
        op.create_index('ix_quizzes_created_at', 'quizzes', ['created_at'], unique=False)
        op.create_index('ix_quizzes_course_module', 'quizzes', ['course_id', 'module_id'], unique=False)
        op.create_index('ix_quizzes_course_active', 'quizzes', ['course_id', 'is_active'], unique=False)
    
    # Create quiz_questions table
    if 'quiz_questions' not in tables:
        op.create_table('quiz_questions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('quiz_id', sa.Integer(), nullable=False),
            sa.Column('question_type', sa.String(length=50), nullable=False),
            sa.Column('question_text', sa.Text(), nullable=False),
            sa.Column('points', sa.Numeric(precision=5, scale=2), nullable=False, server_default='1.0'),
            sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('correct_answer', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'], unique=False)
        op.create_index('ix_quiz_questions_question_type', 'quiz_questions', ['question_type'], unique=False)
        op.create_index('ix_quiz_questions_order_index', 'quiz_questions', ['order_index'], unique=False)
        op.create_index('ix_quiz_questions_quiz_order', 'quiz_questions', ['quiz_id', 'order_index'], unique=False)
    
    # Create quiz_question_options table
    if 'quiz_question_options' not in tables:
        op.create_table('quiz_question_options',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('question_id', sa.Integer(), nullable=False),
            sa.Column('option_text', sa.Text(), nullable=False),
            sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_quiz_question_options_question_id', 'quiz_question_options', ['question_id'], unique=False)
        op.create_index('ix_quiz_question_options_is_correct', 'quiz_question_options', ['is_correct'], unique=False)
        op.create_index('ix_quiz_question_options_order_index', 'quiz_question_options', ['order_index'], unique=False)
        op.create_index('ix_question_options_question_order', 'quiz_question_options', ['question_id', 'order_index'], unique=False)
    
    # Create quiz_attempts table
    if 'quiz_attempts' not in tables:
        op.create_table('quiz_attempts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('quiz_id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('total_points', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('max_points', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'], unique=False)
        op.create_index('ix_quiz_attempts_student_id', 'quiz_attempts', ['student_id'], unique=False)
        op.create_index('ix_quiz_attempts_is_completed', 'quiz_attempts', ['is_completed'], unique=False)
        op.create_index('ix_quiz_attempts_started_at', 'quiz_attempts', ['started_at'], unique=False)
        op.create_index('ix_quiz_attempts_quiz_student', 'quiz_attempts', ['quiz_id', 'student_id'], unique=False)
        op.create_index('ix_quiz_attempts_student_completed', 'quiz_attempts', ['student_id', 'is_completed'], unique=False)
    
    # Create quiz_answers table
    if 'quiz_answers' not in tables:
        op.create_table('quiz_answers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('attempt_id', sa.Integer(), nullable=False),
            sa.Column('question_id', sa.Integer(), nullable=False),
            sa.Column('answer_text', sa.Text(), nullable=True),
            sa.Column('option_id', sa.Integer(), nullable=True),
            sa.Column('is_correct', sa.Boolean(), nullable=True),
            sa.Column('points_earned', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('answered_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['option_id'], ['quiz_question_options.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('attempt_id', 'question_id', name='uq_attempt_question')
        )
        op.create_index('ix_quiz_answers_attempt_id', 'quiz_answers', ['attempt_id'], unique=False)
        op.create_index('ix_quiz_answers_question_id', 'quiz_answers', ['question_id'], unique=False)
        op.create_index('ix_quiz_answers_attempt_question', 'quiz_answers', ['attempt_id', 'question_id'], unique=False)


def downgrade():
    op.drop_index('ix_quiz_answers_attempt_question', table_name='quiz_answers')
    op.drop_index('ix_quiz_answers_question_id', table_name='quiz_answers')
    op.drop_index('ix_quiz_answers_attempt_id', table_name='quiz_answers')
    op.drop_table('quiz_answers')
    
    op.drop_index('ix_quiz_attempts_student_completed', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_quiz_student', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_started_at', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_is_completed', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_student_id', table_name='quiz_attempts')
    op.drop_index('ix_quiz_attempts_quiz_id', table_name='quiz_attempts')
    op.drop_table('quiz_attempts')
    
    op.drop_index('ix_question_options_question_order', table_name='quiz_question_options')
    op.drop_index('ix_quiz_question_options_order_index', table_name='quiz_question_options')
    op.drop_index('ix_quiz_question_options_is_correct', table_name='quiz_question_options')
    op.drop_index('ix_quiz_question_options_question_id', table_name='quiz_question_options')
    op.drop_table('quiz_question_options')
    
    op.drop_index('ix_quiz_questions_quiz_order', table_name='quiz_questions')
    op.drop_index('ix_quiz_questions_order_index', table_name='quiz_questions')
    op.drop_index('ix_quiz_questions_question_type', table_name='quiz_questions')
    op.drop_index('ix_quiz_questions_quiz_id', table_name='quiz_questions')
    op.drop_table('quiz_questions')
    
    op.drop_index('ix_quizzes_course_active', table_name='quizzes')
    op.drop_index('ix_quizzes_course_module', table_name='quizzes')
    op.drop_index('ix_quizzes_created_at', table_name='quizzes')
    op.drop_index('ix_quizzes_order_index', table_name='quizzes')
    op.drop_index('ix_quizzes_is_active', table_name='quizzes')
    op.drop_index('ix_quizzes_module_id', table_name='quizzes')
    op.drop_index('ix_quizzes_course_id', table_name='quizzes')
    op.drop_table('quizzes')
