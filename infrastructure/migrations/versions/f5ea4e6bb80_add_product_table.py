"""add product table

Revision ID: f5ea4e6bb80
Revises: 3830063c1b00
Create Date: 2013-04-17 23:27:05.900923

"""

# revision identifiers, used by Alembic.
revision = 'f5ea4e6bb80'
down_revision = '3830063c1b00'

from alembic import op
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


def upgrade():
    op.create_table('product_collections',
                    Column('id', Integer, primary_key=True),
                    Column('name', String),
                    Column('master', Integer, ForeignKey('product.id'))
                    )

    op.create_table('product_collections_association',
                    Column('product_id', Integer, ForeignKey('product.id')),
                    Column('product_collection_id', Integer, ForeignKey('product_collections.id'))
                    )

    op.create_table('product_flags',
                    Column('id', Integer, primary_key=True),
                    Column('name', String),
                    Column('enabled', Boolean)
                    )

    op.create_table('product_flags_association',
                    Column('product_id', Integer, ForeignKey('product.id')),
                    Column('product_flag_id', Integer, ForeignKey('product_flags.id'))
                    )

    op.create_table('product',
                    Column('id', Integer, primary_key=True),
                    Column('sku', String),
                    Column('name', String),
                    )


def downgrade():
    op.drop_table('product')
    op.drop_table('product_flags_association')
    op.drop_table('product_flags')
    op.drop_table('product_collections_association')
    op.drop_table('product_collections')
