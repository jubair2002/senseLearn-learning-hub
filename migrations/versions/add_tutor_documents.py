"""Add tutor documents table"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '28f14abf02b1'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    tables = inspector.get_table_names()
    if 'tutor_documents' not in tables:
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
        op.create_index(op.f('ix_tutor_documents_tutor_id'), 'tutor_documents', ['tutor_id'], unique=False)
        op.create_index(op.f('ix_tutor_documents_uploaded_at'), 'tutor_documents', ['uploaded_at'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_tutor_documents_uploaded_at'), table_name='tutor_documents')
    op.drop_index(op.f('ix_tutor_documents_tutor_id'), table_name='tutor_documents')
    op.drop_table('tutor_documents')

