"""add_performance_indexes"""
from alembic import op
import sqlalchemy as sa

revision = '28f14abf02b1'
down_revision = '31ccd4145ef5'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('email_verification_otps')]
    if 'ix_email_verification_otps_user_id' not in existing_indexes:
        op.create_index('ix_email_verification_otps_user_id', 'email_verification_otps', ['user_id'], unique=False)
    if 'ix_email_verification_otps_expires_at' not in existing_indexes:
        op.create_index('ix_email_verification_otps_expires_at', 'email_verification_otps', ['expires_at'], unique=False)
    if 'ix_email_verification_otps_created_at' not in existing_indexes:
        op.create_index('ix_email_verification_otps_created_at', 'email_verification_otps', ['created_at'], unique=False)
    if 'ix_email_verification_otps_purpose' not in existing_indexes:
        op.create_index('ix_email_verification_otps_purpose', 'email_verification_otps', ['purpose'], unique=False)
    try:
        if 'ix_email_purpose' not in existing_indexes:
            op.execute("CREATE INDEX ix_email_purpose ON email_verification_otps (email(191), purpose)")
    except: pass
    try:
        if 'ix_user_purpose' not in existing_indexes:
            op.create_index('ix_user_purpose', 'email_verification_otps', ['user_id', 'purpose'], unique=False)
    except: pass
    try:
        if 'ix_email_otp' not in existing_indexes:
            op.execute("CREATE INDEX ix_email_otp ON email_verification_otps (email(191), otp, purpose)")
    except: pass

def downgrade():
    op.drop_index('ix_email_otp', table_name='email_verification_otps')
    op.drop_index('ix_user_purpose', table_name='email_verification_otps')
    op.drop_index('ix_email_purpose', table_name='email_verification_otps')
    op.drop_index('ix_email_verification_otps_purpose', table_name='email_verification_otps')
    op.drop_index('ix_email_verification_otps_created_at', table_name='email_verification_otps')
    op.drop_index('ix_email_verification_otps_expires_at', table_name='email_verification_otps')
    op.drop_index('ix_email_verification_otps_user_id', table_name='email_verification_otps')
