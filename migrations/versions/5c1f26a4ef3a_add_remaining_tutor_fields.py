"""Add remaining tutor fields"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

revision = '5c1f26a4ef3a'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    inspector = inspect(op.get_bind())
    
    # Check if password_reset_codes table exists and add foreign key if needed
    tables = inspector.get_table_names()
    if 'password_reset_codes' in tables:
        try:
    with op.batch_alter_table('password_reset_codes', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])
        except Exception:
            # Foreign key might already exist, skip
            pass
    
    # Check if users table exists and add indexes/constraints if needed
    if 'users' in tables:
        indexes = inspector.get_indexes('users')
        index_names = [idx['name'] for idx in indexes]
        # Check if there's already a unique index on email column
        email_index_exists = any('email' in idx.get('column_names', []) and idx.get('unique', False) for idx in indexes)
        
        unique_constraints = inspector.get_unique_constraints('users')
        username_constraint_exists = any('username' in c.get('column_names', []) for c in unique_constraints)
        
        # Only proceed if we need to create something
        if not email_index_exists or not username_constraint_exists:
            try:
    with op.batch_alter_table('users', schema=None) as batch_op:
                    # Only create index if it doesn't exist
                    if not email_index_exists:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
                    # Only create unique constraint if it doesn't exist
                    if not username_constraint_exists:
        batch_op.create_unique_constraint(None, ['username'])
            except Exception as e:
                # Index or constraint might already exist (error 1061), skip
                # Check if it's a duplicate key error
                error_msg = str(e)
                if '1061' in error_msg or 'Duplicate key' in error_msg or 'duplicate key name' in error_msg.lower():
                    # This is expected - index/constraint already exists
                    pass
                else:
                    # Re-raise if it's a different error
                    raise

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_index(batch_op.f('ix_users_email'))
    with op.batch_alter_table('password_reset_codes', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
