"""add address table

Revision ID: 5aa2dfb6e6a8
Revises: 4b9a79b051c6
Create Date: 2013-03-26 23:47:20.011791

"""

# revision identifiers, used by Alembic.
revision = '5aa2dfb6e6a8'
down_revision = '4b9a79b051c6'

from alembic import op
from sqlalchemy import Column, Integer, String, Enum, ForeignKey


def upgrade():
    enum_types = Enum("BILLING", "SHIPPING", name='address_types')
    enum_types.create(op.get_bind(), checkfirst=False)

    op.create_table('address',
                    Column('id', Integer, primary_key=True),
                    Column('customer_id', Integer, ForeignKey('customer.id')),
                    Column('type', enum_types),
                    Column('line1', String),
                    Column('line2', String),
                    Column('suburb', String),
                    Column('postcode', String),
                    Column('state', String),
                    Column('country', String)
                    )
    # Done implicitly from ForeignKey above
    #op.create_foreign_key('fk_customer_address', 'customer', 'address', ['id'], ['customer_id'])


def downgrade():
    op.drop_table('address')
    Enum(name="address_types").drop(op.get_bind(), checkfirst=False)

    # Happens on drop table above
    #op.drop_constraint('fk_customer_address', 'address', type_='foreignkey')
