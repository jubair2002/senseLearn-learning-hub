"""Add pending registration"""
from alembic import op
import sqlalchemy as sa

revision = '31ccd4145ef5'
down_revision = '85bee21354d6'
branch_labels = None
depends_on = None

def upgrade():
    inspector = sa.inspect(op.get_bind())
    email_otp_columns = [col['name'] for col in inspector.get_columns('email_verification_otps')]
    if 'email' not in email_otp_columns:
        with op.batch_alter_table('email_verification_otps', schema=None) as batch_op:
            batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)
    email_otp_indexes = [idx['name'] for idx in inspector.get_indexes('email_verification_otps')]
    if 'ix_email_verification_otps_email' not in email_otp_indexes:
        with op.batch_alter_table('email_verification_otps', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_email_verification_otps_email'), ['email'], unique=False)
    tables = inspector.get_table_names()
    if 'pending_registrations' not in tables:
        op.create_table('pending_registrations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('registration_data', sa.Text(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    try:
        pending_indexes = [idx['name'] for idx in inspector.get_indexes('pending_registrations')]
        if 'ix_pending_registrations_email' not in pending_indexes:
            op.execute('CREATE UNIQUE INDEX ix_pending_registrations_email ON pending_registrations (email(191))')
    except:
        try:
            op.execute('CREATE UNIQUE INDEX ix_pending_registrations_email ON pending_registrations (email(191))')
        except: pass

def downgrade():
    op.execute('DROP INDEX ix_pending_registrations_email ON pending_registrations')
    op.drop_table('pending_registrations')
    with op.batch_alter_table('email_verification_otps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_email_verification_otps_email'))
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('email')

