"""create customer table

Revision ID: 4b9a79b051c6
Revises: None
Create Date: 2013-03-26 23:34:42.758587

"""

# revision identifiers, used by Alembic.
revision = '4b9a79b051c6'
down_revision = None

from alembic import op
from sqlalchemy import Column, Integer, String


def upgrade():
    op.create_table('customer',
                    Column('id', Integer, primary_key=True),
                    Column('name', String),
                    Column('discount_tier', String),
                    Column('tax_category', String)
                    )


def downgrade():
    op.drop_table('customer')
