"""Add tutor documents table

Revision ID: a1b2c3d4e5f6
Revises: 28f14abf02b1
Create Date: 2025-01-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '28f14abf02b1'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table already exists
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'tutor_documents' not in tables:
        # Create tutor_documents table
        op.create_table('tutor_documents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tutor_id', sa.Integer(), nullable=False),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_type', sa.String(length=50), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=True),
            sa.Column('uploaded_at', sa.DateTime(), nullable=False),
            sa.Column('uploaded_by_admin', sa.Boolean(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['tutor_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        # Create indexes
        op.create_index(op.f('ix_tutor_documents_tutor_id'), 'tutor_documents', ['tutor_id'], unique=False)
        op.create_index(op.f('ix_tutor_documents_uploaded_at'), 'tutor_documents', ['uploaded_at'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_tutor_documents_uploaded_at'), table_name='tutor_documents')
    op.drop_index(op.f('ix_tutor_documents_tutor_id'), table_name='tutor_documents')
    # Drop table
    op.drop_table('tutor_documents')

