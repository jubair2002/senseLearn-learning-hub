"""add target_disability_types to courses table

Revision ID: b2c3d4e5f6a7
Revises: 6cc9963bc796
Create Date: 2025-12-09 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = '6cc9963bc796'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Get columns for courses table
    columns = [col['name'] for col in inspector.get_columns('courses')]
    
    if 'target_disability_types' not in columns:
        # Add target_disability_types column
        op.add_column('courses', 
            sa.Column('target_disability_types', sa.String(length=255), nullable=True)
        )
        # Add index for better query performance
        op.create_index(op.f('ix_courses_target_disability_types'), 'courses', ['target_disability_types'], unique=False)


def downgrade():
    # Drop index
    op.drop_index(op.f('ix_courses_target_disability_types'), table_name='courses')
    # Drop column
    op.drop_column('courses', 'target_disability_types')

