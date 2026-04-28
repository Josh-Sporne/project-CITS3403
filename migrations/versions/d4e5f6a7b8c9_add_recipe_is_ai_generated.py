"""add is_ai_generated to recipe

Revision ID: d4e5f6a7b8c9
Revises: b8d71730109e
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'b8d71730109e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_ai_generated',
                sa.Boolean(),
                nullable=False,
                server_default='0',
            )
        )


def downgrade():
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.drop_column('is_ai_generated')
