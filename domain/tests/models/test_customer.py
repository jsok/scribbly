from unittest import TestCase, skip

from domain.tests.factories.customer import ContactFactory

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
