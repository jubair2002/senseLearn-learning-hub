"""Add chatbot tables

Revision ID: d63d368ba8f1
Revises: 087d31440e61
Create Date: 2026-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd63d368ba8f1'
down_revision = '087d31440e61'
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    tables = inspector.get_table_names()
    
    # Create chat_conversations table
    if 'chat_conversations' not in tables:
        op.create_table('chat_conversations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_chat_conversations_student_id', 'chat_conversations', ['student_id'], unique=False)
        op.create_index('ix_chat_conversations_created_at', 'chat_conversations', ['created_at'], unique=False)
        op.create_index('ix_chat_conversations_updated_at', 'chat_conversations', ['updated_at'], unique=False)
        op.create_index('ix_chat_conversations_is_archived', 'chat_conversations', ['is_archived'], unique=False)
        op.create_index('ix_chat_conversations_student_updated', 'chat_conversations', ['student_id', 'updated_at'], unique=False)
    
    # Create chat_messages table
    if 'chat_messages' not in tables:
        op.create_table('chat_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('conversation_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('message_metadata', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_chat_messages_conversation_id', 'chat_messages', ['conversation_id'], unique=False)
        op.create_index('ix_chat_messages_role', 'chat_messages', ['role'], unique=False)
        op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'], unique=False)
        op.create_index('ix_chat_messages_conversation_created', 'chat_messages', ['conversation_id', 'created_at'], unique=False)


def downgrade():
    op.drop_index('ix_chat_messages_conversation_created', table_name='chat_messages')
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_role', table_name='chat_messages')
    op.drop_index('ix_chat_messages_conversation_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index('ix_chat_conversations_student_updated', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_is_archived', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_updated_at', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_created_at', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_student_id', table_name='chat_conversations')
    op.drop_table('chat_conversations')

