from sqlalchemy import Table, Column, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import mapper, relationship

from infrastructure.persistence import metadata

#  SqlAlchemy Table and Mapping definitions


from domain.model.customer.customer import Customer
customer = Table('customer', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('name', String),
                 Column('discount_tier', String),
                 Column('tax_category', String)
                 )

from domain.model.customer.address import Address
address = Table('address', metadata,
                Column('id', Integer, primary_key=True),
                Column('customer_id', Integer, ForeignKey('customer.id')),
                Column('type', Enum(*Address.TYPE, name='address_types')),
                Column('line1', String),
                Column('line2', String),
                Column('suburb', String),
                Column('postcode', String),
                Column('state', String),
                Column('country', String)
                )

mapper(Customer, customer, properties={
    'addresses': relationship(Address, backref='customer', order_by=address.c.id)
})
mapper(Address, address)
