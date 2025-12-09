"""Add email verification"""
from alembic import op
import sqlalchemy as sa

revision = '85bee21354d6'
down_revision = 'feed7fc04dad'
branch_labels = None
depends_on = None

def upgrade():
    inspector = sa.inspect(op.get_bind())
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'email_verified' not in users_columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'))
    tables = inspector.get_table_names()
    if 'email_verification_otps' not in tables:
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
        indexes = [idx['name'] for idx in inspector.get_indexes('email_verification_otps')]
        if 'ix_email_verification_otps_otp' not in indexes:
            op.create_index(op.f('ix_email_verification_otps_otp'), 'email_verification_otps', ['otp'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_email_verification_otps_otp'), table_name='email_verification_otps')
    op.drop_table('email_verification_otps')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('email_verified')

