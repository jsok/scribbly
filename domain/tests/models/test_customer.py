from unittest import TestCase, skip
from nose.tools import raises

from domain.tests.factories.customer import CustomerFactory, ContactFactory, AddressFactory

class ContactTestCase(TestCase):

    def test_contact_roles(self):
        contact = ContactFactory.build()

        self.assertEquals(0, len(contact.roles), "Contact should not have any rolse")
        self.assertEquals(False, contact.has_role("SALES"), "Contact should not have SALES role")

        contact.add_role("SALES")
        contact.add_role("foo")
        self.assertEquals(True, contact.has_role("SALES"), "Contact should have SALES role")
        self.assertEquals(True, contact.has_role("sales"), "Contact should have SALES role")
        self.assertEquals(False, contact.has_role("ACCOUNTS"), "Contact should not have ACCOUNTS role")
        self.assertEquals(False, contact.has_role("foo"), "Contact should not have ACCOUNTS role")

    def test_contact_phones(self):
        contact = ContactFactory.build()

        contact.add_phone("OFFICE", "+61290001111")
        contact.add_phone("MOBILE", "+61400111222")
        contact.add_phone("foo", "+61400111222")

        self.assertIsNone(contact.get_phone("OTHER"), "No phone number should be registered with OTHER type")
        self.assertIsNone(contact.get_phone("foo"), "No phone number should be registered with OTHER type")
        self.assertIsNotNone(contact.get_phone("MOBILE"), "MOBILE phone entry not found")
        self.assertIsNotNone(contact.get_phone("OFFICE"), "OFFICE phone entry not found")


class AddressTestCase(TestCase):

    def test_address_types(self):
        shipping = AddressFactory.build(type="SHIPPING")
        billing = AddressFactory.build(type="billing")

        self.assertTrue(shipping.is_type("SHIPPING"), "Shipping address has wrong type")
        self.assertTrue(billing.is_type("BILLING"), "Billing address has wrong type")

    @raises(ValueError)
    def test_address_type_invalid(self):
        address = AddressFactory.build(type="foo")


class CustomerTestCase(TestCase):

    def test_customer_one_contact_per_role(self):
        customer = CustomerFactory.build()
        sales_contact = ContactFactory.build(firstname="Sales")
        sales_contact.add_role("SALES")

        acct_contact = ContactFactory.build(firstname="Accounts")
        acct_contact.add_role("ACCOUNTS")

        customer.add_contact(sales_contact)
        customer.add_contact(acct_contact)
        customer.add_contact("XXX")

        self.assertEquals(2, len(customer.contacts), "Wrong number of contacts added to customer")

        sales_contacts = customer.get_contacts("SALES")
        self.assertEquals(1, len(sales_contacts), "Could not find any sales contacts")
        self.assertEquals("Sales", sales_contacts[0].firstname, "Found wrong sales contacts")

        acct_contacts = customer.get_contacts("ACCOUNTS")
        self.assertEquals(1, len(acct_contacts), "Could not find any accounts contacts")
        self.assertEquals("Accounts", acct_contacts[0].firstname, "Found wrong accounts contacts")

    def test_customer_addresses(self):
        customer = CustomerFactory.build()
        shipping = AddressFactory.build(type="SHIPPING")
        billing = AddressFactory.build(type="BILLING")

        customer.add_address(shipping)
        customer.add_address(billing)
        customer.add_address("1 Main St, City")

        shipping_addresses = customer.get_addresses("SHIPPING")
        billing_addresses = customer.get_addresses("BILLING")

        self.assertEquals(1, len(shipping_addresses), "No shipping addresses found")
        self.assertEquals(1, len(billing_addresses), "No billing addresses found")

    def test_customer_sales_history(self):
        customer = CustomerFactory.build()

        customer.submit_order("ORD001")
        customer.submit_order("ORD002")
        customer.submit_invoice("INV001")

        self.assertTrue("ORD001" in customer.orders, "ORD001 not found in customer sales history")
        self.assertTrue("ORD002" in customer.orders, "ORD002 not found in customer sales history")
        self.assertTrue("INV001" in customer.invoices, "INV001 not found in customer sales history")

        self.assertFalse("INVXXX" in customer.invoices, "Non-existant invoice found in customer sales history")