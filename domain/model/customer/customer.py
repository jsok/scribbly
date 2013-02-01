from domain.shared.entity import Entity

from domain.model.customer.address import Address
from domain.model.customer.contact import Contact

class Customer(Entity):
    """
    A customer is an aggregate root for all contact details and sales history for a single customer.
    """

    def __init__(self, name):
        self.name = name
        self.contacts = []
        self.addresses = []

    def add_contact(self, contact):
        if isinstance(contact, Contact):
            self.contacts.append(contact)

    def get_contacts(self, role):
        return [contact for contact in self.contacts if contact.has_role(role)]

    def add_address(self, address):
        if isinstance(address, Address):
            self.addresses.append(address)

    def get_addresses(self, type):
        return [address for address in self.addresses if address.is_type(type)]