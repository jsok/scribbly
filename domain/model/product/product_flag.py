from domain.shared.entity import Entity


class ProductFlag(Entity):
    def __init__(self, name, enabled=None):
        self.name = name
        self.enabled = enabled if enabled is True else False
        self.products = []

    def set_flag(self, value):
        self.enabled = value if value is True else False

    def get_flag(self):
        return self.enabled