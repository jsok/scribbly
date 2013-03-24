from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper

from infrastructure.persistence import metadata

#  SqlAlchemy Table and Mapping definitions


customer = Table('customer', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('name', String),
                 Column('discount_tier', String),
                 Column('tax_category', String))

from domain.model.customer.customer import Customer
mapper(Customer, customer)
