from domain.shared.entity import Entity

from domain.model.customer.contact import Contact

class Customer(Entity):
    """
    A customer is an aggregate root for all contact details and sales history for a single customer.
    """

    def __init__(self, name):
        self.name = name
        self.contacts = []

    def add_contact(self, contact):
        if isinstance(contact, Contact):
            self.contacts.append(contact)

    def get_contacts(self, role):
        return [contact for contact in self.contacts if contact.has_role(role)]