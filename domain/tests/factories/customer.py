import factory

from domain.model.customer import contact

class ContactFactory(factory.Factory):
    FACTORY_FOR = contact.Contact

    firstname = "First"
    lastname = "Last"
    email = "first.last@example.com"
