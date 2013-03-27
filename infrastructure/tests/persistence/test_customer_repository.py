from domain.tests.factories.customer import CustomerFactory, AddressFactory

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

    def test_add_address(self):
        customer = CustomerFactory.build(name="Customer")
        self.repository.store(customer)

        biling_address = AddressFactory.build(type="BILLING")
        customer.add_address(biling_address)

        # Create a shipping address, persist it in a new session
        shipping_address = AddressFactory.build(type="Shipping")
        customer.add_address(shipping_address)

        c = self.repository.find("Customer")
        a = c.get_addresses("BILLING")
        self.assertIsNotNone(c)
        self.assertEquals(1, len(a), "Customer should only have 1 billing address")
        self.assertTrue(biling_address == a[0], "Billing addresses don't match")

        a = c.get_addresses("SHIPPING")
        self.assertEquals(1, len(a), "Customer should only have 1 shipping addresses")