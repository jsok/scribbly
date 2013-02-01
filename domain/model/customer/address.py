from domain.shared.entity import Entity

class Address(Entity):

    TYPE = ["BILLING", "SHIPPING"]

    def __init__(self, line1, line2, suburb, postcode, state, type, country=None):
        self.line1 = line1
        self.line2 = line2
        self.suburb = suburb
        self.postcode = postcode
        self.state = state

        if type.upper() not in self.TYPE:
            raise ValueError()
        self.type = type.upper()

        self.country = country if country else None

    def is_type(self, type):
        return self.type == type.upper()