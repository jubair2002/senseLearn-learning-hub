"""Add chatbot documents table

Revision ID: fdfa9005a629
Revises: d63d368ba8f1
Create Date: 2026-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'fdfa9005a629'
down_revision = 'd63d368ba8f1'
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    tables = inspector.get_table_names()
    
    # Create chatbot_documents table
    if 'chatbot_documents' not in tables:
        # Create table without foreign key constraints first
        # We'll add foreign key constraints separately using raw SQL to avoid type mismatches
        op.create_table('chatbot_documents',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('conversation_id', sa.Integer(), nullable=True),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.Column('original_filename', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_type', sa.String(length=50), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('extracted_text', sa.Text(), nullable=True),
            sa.Column('audio_path', sa.String(length=500), nullable=True),
            sa.Column('uploaded_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_chatbot_documents_student_uploaded', 'chatbot_documents', ['student_id', 'uploaded_at'], unique=False)
        op.create_index('ix_chatbot_documents_conversation', 'chatbot_documents', ['conversation_id'], unique=False)
        op.create_index('ix_chatbot_documents_student_id', 'chatbot_documents', ['student_id'], unique=False)
        op.create_index('ix_chatbot_documents_uploaded_at', 'chatbot_documents', ['uploaded_at'], unique=False)
        
        # Add foreign key constraints using raw SQL to ensure compatibility
        # This approach avoids data type mismatches
        connection = op.get_bind()
        
        # Add foreign key for student_id
        try:
            connection.execute(sa.text(
                "ALTER TABLE chatbot_documents "
                "ADD CONSTRAINT fk_chatbot_documents_student_id "
                "FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE"
            ))
        except Exception as e:
            import warnings
            warnings.warn(f"Could not create foreign key constraint for student_id: {e}")
        
        # Add foreign key for conversation_id if chat_conversations exists
        if 'chat_conversations' in tables:
            try:
                connection.execute(sa.text(
                    "ALTER TABLE chatbot_documents "
                    "ADD CONSTRAINT fk_chatbot_documents_conversation_id "
                    "FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE"
                ))
            except Exception as e:
                import warnings
                warnings.warn(f"Could not create foreign key constraint for conversation_id: {e}")


def downgrade():
    op.drop_index('ix_chatbot_documents_uploaded_at', table_name='chatbot_documents')
    op.drop_index('ix_chatbot_documents_student_id', table_name='chatbot_documents')
    op.drop_index('ix_chatbot_documents_conversation', table_name='chatbot_documents')
    op.drop_index('ix_chatbot_documents_student_uploaded', table_name='chatbot_documents')
    op.drop_table('chatbot_documents')

