"""Add student file progress tracking table

Revision ID: c18751849cce
Revises: c3d4e5f6a7b8
Create Date: 2025-12-11 10:20:30.311044

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c18751849cce'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table already exists (in case it was created manually)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'student_file_progress' not in existing_tables:
        # Only create the student_file_progress table if it doesn't exist
        op.create_table('student_file_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.Column('file_id', sa.Integer(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('first_viewed_at', sa.DateTime(), nullable=False),
            sa.Column('last_viewed_at', sa.DateTime(), nullable=False),
            sa.Column('view_count', sa.Integer(), nullable=False, server_default='1'),
            sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['file_id'], ['module_files.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('student_id', 'file_id', name='uq_student_file_progress'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_student_file_progress_student_course', 'student_file_progress', ['student_id', 'course_id'], unique=False)
        op.create_index('ix_student_file_progress_course_student', 'student_file_progress', ['course_id', 'student_id'], unique=False)
    else:
        # Table already exists, just ensure indexes exist
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('student_file_progress')]
        if 'ix_student_file_progress_student_course' not in existing_indexes:
            op.create_index('ix_student_file_progress_student_course', 'student_file_progress', ['student_id', 'course_id'], unique=False)
        if 'ix_student_file_progress_course_student' not in existing_indexes:
            op.create_index('ix_student_file_progress_course_student', 'student_file_progress', ['course_id', 'student_id'], unique=False)


def downgrade():
    # Drop the student_file_progress table
    op.drop_index('ix_student_file_progress_course_student', table_name='student_file_progress')
    op.drop_index('ix_student_file_progress_student_course', table_name='student_file_progress')
    op.drop_table('student_file_progress')
