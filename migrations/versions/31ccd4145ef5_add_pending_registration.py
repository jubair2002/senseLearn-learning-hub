"""Add pending registration

Revision ID: 31ccd4145ef5
Revises: 85bee21354d6
Create Date: 2025-01-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '31ccd4145ef5'
down_revision = '85bee21354d6'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Add email column to email_verification_otps and make user_id nullable
    email_otp_columns = [col['name'] for col in inspector.get_columns('email_verification_otps')]
    if 'email' not in email_otp_columns:
        with op.batch_alter_table('email_verification_otps', schema=None) as batch_op:
            batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)
    
    # Check if email index exists
    email_otp_indexes = [idx['name'] for idx in inspector.get_indexes('email_verification_otps')]
    if 'ix_email_verification_otps_email' not in email_otp_indexes:
        with op.batch_alter_table('email_verification_otps', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_email_verification_otps_email'), ['email'], unique=False)

    # Check if pending_registrations table exists
    tables = inspector.get_table_names()
    if 'pending_registrations' not in tables:
        # Create pending_registrations table
        op.create_table('pending_registrations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('registration_data', sa.Text(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Check if index exists, if not create it with prefix
    try:
        pending_indexes = [idx['name'] for idx in inspector.get_indexes('pending_registrations')]
        if 'ix_pending_registrations_email' not in pending_indexes:
            # Use prefix index for email to avoid MySQL key length limit
            # Index first 191 characters (safe for UTF8MB4: 191 * 4 = 764 bytes < 1000)
            op.execute('CREATE UNIQUE INDEX ix_pending_registrations_email ON pending_registrations (email(191))')
    except Exception:
        # Index might already exist, try to create it anyway (will fail gracefully if exists)
        try:
            op.execute('CREATE UNIQUE INDEX ix_pending_registrations_email ON pending_registrations (email(191))')
        except Exception:
            pass  # Index already exists


def downgrade():
    # Drop pending_registrations table
    op.execute('DROP INDEX ix_pending_registrations_email ON pending_registrations')
    op.drop_table('pending_registrations')

    # Revert email_verification_otps changes
    with op.batch_alter_table('email_verification_otps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_email_verification_otps_email'))
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('email')

