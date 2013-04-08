from domain.shared.entity import Entity


class Contact(Entity):
    """
    A person within the customer organisation and all their details.
    """

    def __init__(self, firstname, lastname, email):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email

        self.roles = []
        self.phones = {}

    def add_role(self, role):
        self.roles.append(ContactRole(role))

    def has_role(self, role):
        return len([r for r in self.roles if r.role == role.upper()]) == 1

    def add_phone(self, type, number):
        self.phones.update({type.upper(): ContactPhone(type, number)})

    def get_phone(self, type):
        return self.phones.get(type.upper(), None)


class ContactRole(Entity):
    ROLES = ["SALES", "ACCOUNTS"]

    def __init__(self, role):
        self.role = role.upper()


class ContactPhone(Entity):
    PHONES = ["OFFICE", "MOBILE", "OTHER"]

    def __init__(self, type, number):
        self.type = type
        self.number = number