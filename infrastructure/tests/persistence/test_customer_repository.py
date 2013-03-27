from unittest import TestCase

from domain.tests.factories.customer import CustomerFactory

from infrastructure.tests.persistence import PersistenceTestCase
from infrastructure.persistence.customer_repository import CustomerRepository


class CustomerRepositoryTestCase(PersistenceTestCase):
    def setUp(self):
        super(CustomerRepositoryTestCase, self).setUp()
        self.repository = CustomerRepository(self.session)

    def test_add_customer(self):
        customer = CustomerFactory.build(name="Customer")

        self.repository.store(customer)

        c = self.repository.find("Customer")
        self.assertIsNotNone(c)
        self.assertEquals("Customer", c.name)

    def test_rollback_performed(self):
        c = self.repository.find("Customer")
        self.assertIsNone(c)
