import factory

from domain.model.customer import customer, contact, address


class CustomerFactory(factory.Factory):
    FACTORY_FOR = customer.Customer
    FACTORY_STRATEGY = 'build'

    name = "Customer Name"
    discount_tier = "GRADE-A"
    tax_category = "GST"


class ContactFactory(factory.Factory):
    FACTORY_FOR = contact.Contact
    FACTORY_STRATEGY = 'build'

    firstname = "First"
    lastname = "Last"
    email = "first.last@example.com"


class AddressFactory(factory.Factory):
    FACTORY_FOR = address.Address
    FACTORY_STRATEGY = 'build'

    line1 = "Unit 1"
    line2 = "2 Street St"
    suburb = "Suburb"
    postcode = "2000"
    state = "NSW"
    country = "Australia"
    type = "BILLING"