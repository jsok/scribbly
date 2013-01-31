from domain.shared.entity import Entity

class Contact(Entity):
    """
    A person within the customer organisation and all their details.
    """

    ROLES = ["SALES", "ACCOUNTS"]
    PHONES = ["OFFICE", "MOBILE", "OTHER"]

    def __init__(self, firstname, lastname, email):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email

        self.roles = set()
        self.phones = {}

    def add_role(self, role):
        if role.upper() in self.ROLES:
            self.roles.add(role.upper())

    def has_role(self, role):
        return role.upper() in self.roles

    def add_phone(self, type, number):
        if type.upper() in self.PHONES:
            self.phones.update({type.upper(): number})

    def get_phone(self, type):
        return self.phones.get(type.upper(), None)