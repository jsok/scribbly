from domain.shared.entity import Entity


class TaxRate(Entity):
    """
    Tax rate which can be applied to line items in sales documents.
    """

    def __init__(self, name, rate):
        self.name = name

        if not 0.00 <= rate < 1.00:
            raise ValueError("Tax rate must between 0% and 99%")
        self.rate = rate