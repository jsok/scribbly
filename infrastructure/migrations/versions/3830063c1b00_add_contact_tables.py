"""add contact tables

Revision ID: 3830063c1b00
Revises: 5aa2dfb6e6a8
Create Date: 2013-04-08 21:09:49.102414

"""

# revision identifiers, used by Alembic.
revision = '3830063c1b00'
down_revision = '5aa2dfb6e6a8'

from alembic import op
from sqlalchemy import Column, Integer, String, Enum, ForeignKey


def upgrade():
    enum_roles = Enum("SALES", "ACCOUNTS", name='role_types')
    enum_roles.create(op.get_bind(), checkfirst=False)

    op.create_table('contact_roles',
                    Column('id', Integer, primary_key=True),
                    Column('role', enum_roles)
                    )

    enum_phones = Enum("OFFICE", "MOBILE", "OTHER", name='phone_types')
    enum_phones.create(op.get_bind(), checkfirst=False)

    op.create_table('contact_phones',
                    Column('id', Integer, primary_key=True,),
                    Column('contact_id', Integer, ForeignKey('contact.id')),
                    Column('type', enum_phones),
                    Column('number', String)
                    )

    op.create_table('contact_roles_association',
                    Column('contact_id', Integer, ForeignKey('contact.id')),
                    Column('contact_roles_id', Integer, ForeignKey('contact_roles.id'))
                    )

    op.create_table('contact',
                    Column('id', Integer, primary_key=True),
                    Column('customer_id', Integer, ForeignKey('customer.id')),
                    Column('firstname', String),
                    Column('lastname', String),
                    Column('email', String),
                    )


def downgrade():
    op.drop_table('contact_roles')
    Enum(name="role_types").drop(op.get_bind(), checkfirst=False)
    op.drop_table('contact_phones')
    Enum(name="phone_types").drop(op.get_bind(), checkfirst=False)
    op.drop_table('contact_roles_association')
    op.drop_table('contact')
