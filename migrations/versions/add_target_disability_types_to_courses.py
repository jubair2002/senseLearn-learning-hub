"""add target_disability_types to courses table"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = '6cc9963bc796'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('courses')]
    if 'target_disability_types' not in columns:
        op.add_column('courses', sa.Column('target_disability_types', sa.String(length=255), nullable=True))
        op.create_index(op.f('ix_courses_target_disability_types'), 'courses', ['target_disability_types'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_courses_target_disability_types'), table_name='courses')
    op.drop_column('courses', 'target_disability_types')

