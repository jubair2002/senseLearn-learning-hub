"""add course modules and module files

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-09 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # Check if tables already exist
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'course_modules' not in tables:
        # Create course_modules table
        op.create_table('course_modules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        # Create indexes
        op.create_index(op.f('ix_course_modules_course_id'), 'course_modules', ['course_id'], unique=False)
        op.create_index(op.f('ix_course_modules_order_index'), 'course_modules', ['order_index'], unique=False)
        op.create_index(op.f('ix_course_modules_created_at'), 'course_modules', ['created_at'], unique=False)
        op.create_index(op.f('ix_course_modules_course_order'), 'course_modules', ['course_id', 'order_index'], unique=False)
    
    if 'module_files' not in tables:
        # Create module_files table
        op.create_table('module_files',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('module_id', sa.Integer(), nullable=False),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_type', sa.String(length=50), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=True),
            sa.Column('uploaded_at', sa.DateTime(), nullable=False),
            sa.Column('uploaded_by', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        # Create unique index with prefix for file_path (MySQL key length limit)
        op.create_index('uq_module_files_file_path', 'module_files', ['file_path'], unique=True, mysql_length={'file_path': 191})
        # Create indexes
        op.create_index(op.f('ix_module_files_module_id'), 'module_files', ['module_id'], unique=False)
        op.create_index(op.f('ix_module_files_file_type'), 'module_files', ['file_type'], unique=False)
        op.create_index(op.f('ix_module_files_uploaded_at'), 'module_files', ['uploaded_at'], unique=False)
        op.create_index(op.f('ix_module_files_module_uploaded'), 'module_files', ['module_id', 'uploaded_at'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('uq_module_files_file_path', table_name='module_files')
    op.drop_index(op.f('ix_module_files_module_uploaded'), table_name='module_files')
    op.drop_index(op.f('ix_module_files_uploaded_at'), table_name='module_files')
    op.drop_index(op.f('ix_module_files_file_type'), table_name='module_files')
    op.drop_index(op.f('ix_module_files_module_id'), table_name='module_files')
    # Drop module_files table
    op.drop_table('module_files')
    
    # Drop indexes
    op.drop_index(op.f('ix_course_modules_course_order'), table_name='course_modules')
    op.drop_index(op.f('ix_course_modules_created_at'), table_name='course_modules')
    op.drop_index(op.f('ix_course_modules_order_index'), table_name='course_modules')
    op.drop_index(op.f('ix_course_modules_course_id'), table_name='course_modules')
    # Drop course_modules table
    op.drop_table('course_modules')

