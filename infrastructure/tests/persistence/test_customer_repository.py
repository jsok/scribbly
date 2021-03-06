from nose.tools import raises
from sqlalchemy.exc import IntegrityError
from nose_alembic_attrib import alembic_attr

from domain.tests.factories.customer import CustomerFactory, AddressFactory, ContactFactory

from infrastructure.tests.persistence import PersistenceTestCase
from infrastructure.persistence.customer_repository import CustomerRepository


class CustomerRepositoryTestCase(PersistenceTestCase):
    def setUp(self):
        super(CustomerRepositoryTestCase, self).setUp()
        self.repository = CustomerRepository(self.session)

    @alembic_attr(minimum_revision="4b9a79b051c6")
    def test_add_customer(self):
        customer = CustomerFactory.build(name="Customer")

        self.repository.store(customer)

        c = self.repository.find("Customer")
        self.assertIsNotNone(c)
        self.assertEquals("Customer", c.name)

    @alembic_attr(minimum_revision="4b9a79b051c6")
    def test_rollback_performed(self):
        c = self.repository.find("Customer")
        self.assertIsNone(c)

    @alembic_attr(minimum_revision="5aa2dfb6e6a8")
    def test_add_address(self):
        customer = CustomerFactory.build(name="Customer")
        self.repository.store(customer)

        billing_address = AddressFactory.build(type="BILLING")
        customer.add_address(billing_address)

        shipping_address = AddressFactory.build(type="SHIPPING")
        customer.add_address(shipping_address)

        c = self.repository.find("Customer")
        a = c.get_addresses("BILLING")
        self.assertIsNotNone(c)
        self.assertEquals(1, len(a), "Customer should only have 1 billing address")
        self.assertEqual(billing_address, a[0], "Billing addresses don't match")

        a = c.get_addresses("SHIPPING")
        self.assertEquals(1, len(a), "Customer should only have 1 shipping addresses")
        self.assertEqual(shipping_address, a[0], "Shipping addresses don't match")

    @alembic_attr(minimum_revision="3830063c1b00")
    def test_add_contact(self):
        customer = CustomerFactory.build(name="Customer")
        self.repository.store(customer)

        contact = ContactFactory.build()
        contact.add_role("SALES")
        contact.add_phone("OFFICE", "+6129000000")
        customer.add_contact(contact)

    @alembic_attr(minimum_revision="3830063c1b00")
    @raises(IntegrityError)
    def test_add_contact_role_non_enum(self):
        customer = CustomerFactory.build(name="Customer")
        contact = ContactFactory.build()
        contact.add_role("FOO")

        customer.add_contact(contact)
        self.repository.store(customer)


    @alembic_attr(minimum_revision="3830063c1b00")
    @raises(IntegrityError)
    def test_add_contact_phone_non_enum(self):
        customer = CustomerFactory.build(name="Customer")
        contact = ContactFactory.build()
        contact.add_phone("FOO", "1111111")

        customer.add_contact(contact)
        self.repository.store(customer)
