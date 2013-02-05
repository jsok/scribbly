from domain.shared.entity import Entity

from domain.model.customer.address import Address
from domain.model.customer.contact import Contact

class Customer(Entity):
    """
    A customer is an aggregate root for all contact details and sales history for a single customer.
    """

    def __init__(self, name, discount_tier, tax_category=None):
        self.name = name
        self.contacts = []
        self.addresses = []

        self.orders = set()
        self.invoices = set()

        self.discount_tier = discount_tier
        self.tax_category = tax_category if tax_category else None

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

    def submit_order(self, order_id):
        self.orders.add(order_id)

    def submit_invoice(self, invoice_id):
        self.invoices.add(invoice_id)