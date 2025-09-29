"""Add categories table and modify products table

Revision ID: 001
Revises: 
Create Date: 2025-09-29 22:18:22.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('featured', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Add category_id to products table
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_hot_product', sa.Boolean(), nullable=True))
        batch_op.create_foreign_key('fk_products_category_id', 'categories', ['category_id'], ['id'])


def downgrade():
    # Remove foreign key constraint first
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('fk_products_category_id', type_='foreignkey')
        batch_op.drop_column('is_hot_product')
        batch_op.drop_column('category_id')

    # Drop categories table
    op.drop_table('categories')