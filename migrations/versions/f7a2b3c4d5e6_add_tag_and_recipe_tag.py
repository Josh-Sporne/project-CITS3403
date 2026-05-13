"""add Tag and RecipeTag tables for multi-tag support (C14)

Revision ID: f7a2b3c4d5e6
Revises: d4e5f6a7b8c9
Create Date: 2026-05-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7a2b3c4d5e6'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_tag_name'), 'tag', ['name'], unique=True)

    op.create_table(
        'recipe_tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recipe_id', 'tag_id', name='uq_recipe_tag'),
    )
    op.create_index(op.f('ix_recipe_tag_recipe_id'), 'recipe_tag', ['recipe_id'], unique=False)
    op.create_index(op.f('ix_recipe_tag_tag_id'), 'recipe_tag', ['tag_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_recipe_tag_tag_id'), table_name='recipe_tag')
    op.drop_index(op.f('ix_recipe_tag_recipe_id'), table_name='recipe_tag')
    op.drop_table('recipe_tag')
    op.drop_index(op.f('ix_tag_name'), table_name='tag')
    op.drop_table('tag')
