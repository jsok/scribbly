from sqlalchemy import create_engine
from unittest import TestCase

from domain.tests.factories.customer import CustomerFactory

from infrastructure.persistence import Session, metadata
from infrastructure.persistence.customer_repository import CustomerRepository


class CustomerRepositoryTestCase(TestCase):

    def setUp(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        Session.configure(bind=engine)

        metadata.create_all(engine)

        self.repository = CustomerRepository()

    def tearDown(self):
        self.repository.session.rollback()

    def test_add_customer(self):
        customer = CustomerFactory.build(name="Customer")

        self.repository.store(customer)

        c = self.repository.find("Customer")
        self.assertIsNotNone(c)
        self.assertEquals("Customer", c.name)

    def test_rollback_performed(self):
        c = self.repository.find("Customer")
        self.assertIsNone(c)