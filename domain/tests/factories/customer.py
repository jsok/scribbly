import factory

from domain.model.customer import customer, contact

class CustomerFactory(factory.Factory):
    FACTORY_FOR = customer.Customer

    name = "Customer Name"

class ContactFactory(factory.Factory):
    FACTORY_FOR = contact.Contact

    firstname = "First"
    lastname = "Last"
    email = "first.last@example.com"
