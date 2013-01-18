from domain.shared.entity import Entity

class Warehouse(Entity):
    def __init__(self, name):
        self.name = name
        self.can_fulfill_orders = True
        self.items = {}
