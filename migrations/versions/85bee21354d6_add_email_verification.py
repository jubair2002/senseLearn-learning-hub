"""Add email verification

Revision ID: 85bee21354d6
Revises: feed7fc04dad
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '85bee21354d6'
down_revision = 'feed7fc04dad'
branch_labels = None
depends_on = None


def upgrade():
    # Check and add email_verified column to users table if it doesn't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'email_verified' not in users_columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'))

    # Check if email_verification_otps table exists
    tables = inspector.get_table_names()
    if 'email_verification_otps' not in tables:
        # Create email_verification_otps table
        op.create_table('email_verification_otps',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('otp', sa.String(length=20), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('purpose', sa.String(length=50), nullable=False, server_default='verification'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_email_verification_otps_otp'), 'email_verification_otps', ['otp'], unique=False)
    else:
        # Table exists, just ensure the index exists
        indexes = [idx['name'] for idx in inspector.get_indexes('email_verification_otps')]
        if 'ix_email_verification_otps_otp' not in indexes:
            op.create_index(op.f('ix_email_verification_otps_otp'), 'email_verification_otps', ['otp'], unique=False)


def downgrade():
    # Drop email_verification_otps table
    op.drop_index(op.f('ix_email_verification_otps_otp'), table_name='email_verification_otps')
    op.drop_table('email_verification_otps')

    # Remove email_verified column from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('email_verified')

