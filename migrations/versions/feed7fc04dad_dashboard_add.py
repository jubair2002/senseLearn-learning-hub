"""dashboard add"""
from alembic import op
import sqlalchemy as sa

revision = 'feed7fc04dad'
down_revision = '5c1f26a4ef3a'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('password_reset_codes', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
        batch_op.create_unique_constraint(None, ['username'])

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_index(batch_op.f('ix_users_email'))
    with op.batch_alter_table('password_reset_codes', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
