from sqlalchemy import Table, Column, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import mapper, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from infrastructure.persistence import metadata

from domain.model.customer.customer import Customer
from domain.model.customer.contact import Contact
from domain.model.customer.contact import ContactPhone
from domain.model.customer.contact import ContactRole

#  SqlAlchemy Table and Mapping definitions

customer = \
    Table('customer', metadata,
          Column('id', Integer, primary_key=True),
          Column('name', String),
          Column('discount_tier', String),
          Column('tax_category', String)
          )

from domain.model.customer.address import Address
address = \
    Table('address', metadata,
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

contact_roles = \
    Table('contact_roles', metadata,
          Column('id', Integer, primary_key=True),
          Column('role', Enum(*ContactRole.ROLES, name='role_types'))
          )
mapper(ContactRole, contact_roles)

# M2M association between contact and contact roles
contact_roles_association = \
    Table('contact_roles_association', metadata,
          Column('contact_id', Integer, ForeignKey('contact.id')),
          Column('contact_roles_id', Integer, ForeignKey('contact_roles.id'))
          )

contact_phones = \
    Table('contact_phones', metadata,
          Column('id', Integer, primary_key=True,),
          Column('contact_id', Integer, ForeignKey('contact.id')),
          Column('type', Enum(*ContactPhone.PHONES, name='phone_types')),
          Column('number', String)
          )
mapper(ContactPhone, contact_phones)

contact = \
    Table('contact', metadata,
          Column('id', Integer, primary_key=True),
          Column('customer_id', Integer, ForeignKey('customer.id')),
          Column('firstname', String),
          Column('lastname', String),
          Column('email', String),
          )

mapper(Customer, customer, properties={
    'addresses': relationship(Address, backref='customer', order_by=address.c.id),
    'contacts': relationship(Contact, backref='customer', order_by=contact.c.id)
})

mapper(Address, address)
mapper(Contact, contact, properties={
    'roles': relationship(ContactRole, secondary=contact_roles_association),
    'phones': relationship(ContactPhone,
                           collection_class=attribute_mapped_collection(contact_phones.c.type))
})
