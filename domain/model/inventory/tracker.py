import functools
import operator

class TrackingStateMachine(object):

    def __init__(self):
        self.states = {}
        self.transitions = {}

    def state(self, name):
        return self.states.get(name, None)

    def add_state(self, state):
        if not isinstance(state, TrackingState):
            raise TypeError()
        self.states.update({ state.name: state })

    def transition(self, name, from_item_dict, to_item_dict):
        """
        Retrieve the transition function and curry in the to_state.
        Validate the items being passed into each state.
        """
        null_op = lambda: None
        if not self.transitions.has_key(name):
            return null_op

        from_state, to_state = self.transitions.get(name)
        from_item = from_state._validated_item(from_item_dict)
        to_item = to_state._validated_item(to_item_dict)
        if not from_item or not to_item:
            return null_op

        transition = getattr(from_state, name)
        return functools.partial(transition, to_state, from_item, to_item)

    def add_transition(self, name, from_state, to_state):
        """
        Add a transition between two states.
        The name is taken to be a method on the from_state.
        """
        from_state = self.states.get(from_state, None)
        to_state = self.states.get(to_state, None)

        if not (from_state and to_state):
            raise ValueError()

        if hasattr(from_state, name) and callable(getattr(from_state, name)):
            self.transitions.update({ name: (from_state, to_state) })
        else:
            raise ValueError()


class TrackingState(object):

    class TrackingItem(object):
        def __init__(self):
            self.validations = []

        def validate(self):
            """
            Apply each rule to the item and only succeed if all validations pass.
            """
            return reduce(operator.and_, map(lambda f: f(self), self.validations), True)

    def __init__(self, name, item_type):
        self.name = name
        self.item_type = item_type

    def _validated_item(self, item_dict):
        item = self.item_type(item_dict)
        return item if item.validate() else None

    def track(self, item):
        """
        Track an item in this state.
        An item cannot be 'untracked', items only move between states via transitions.
        Item may either be a dictionary, or an item if being called internally.
        If a dictionary, we must perform any necessary validations before tracking is allowed.
        Do not override, see _track method instead.
        """
        if not isinstance(item, self.item_type):
            item = self._validated_item(item)
        if item:
            self._track(item)

    def _track(self, item):
        """
        Internal track method all implementors provide.
        """
        raise NotImplementedError() # pragma: no cover

    def quantity(self, key=None):
        """
        Quantity of items tracked, most implementors will have additional keys to filter on.
        """
        raise NotImplementedError() # pragma: no cover


class OnHandState(TrackingState):

    class OnHandItem(TrackingState.TrackingItem):
        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.warehouse = properties.get("warehouse", None)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
                (lambda i: i.warehouse is not None),
                ])


    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.OnHandItem)
        self.items = {}

    def _track(self, item):
        new_quantity = item.quantity + self.items.get(item.warehouse, 0)
        self.items.update({ item.warehouse: new_quantity })

    def quantity(self, warehouse=None):
        if warehouse:
            return self.items.get(warehouse, 0)
        else:
            return reduce(operator.add, [qty for qty in self.items.values()], 0)

    def _reduce_quantity_for(self, warehouse, quantity):
        current_quantity = self.items.get(warehouse)
        self.items.update({ warehouse: current_quantity - quantity })

    def commit(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def allocate(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.warehouse, from_item.quantity)
        to_state.track(to_item)


class CommittedState(TrackingState):

    class CommittedItem(TrackingState.TrackingItem):
        """
        When an order is acknowledged, it will commit items from the inventory.
        A committed item affects on-hand count and will eventually be shipped.
        """
        def __init__(self, properties):
            import datetime

            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.warehouse = properties.get("warehouse", None)
            self.date = properties.get("date", datetime.datetime.now())
            self.order_id = properties.get("order_id", None)

            self.validations.extend([
                (lambda i: i.quantity > 0),
                (lambda i: i.warehouse is not None),
                (lambda i: i.date is not None),
                (lambda i: i.order_id is not None),
                ])


    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.CommittedItem)
        self.items = {}
        # items is dict of dict: { order_id: { warehouse: item } }

    def _track(self, item):
        if self.items.has_key(item.order_id):
            self.items.get(item.order_id).update({ item.warehouse: item })
        else:
            self.items[item.order_id] = { item.warehouse: item }

    def get(self, order_id):
        return self.items.get(order_id, None)

    def quantity(self, warehouse=None):
        quantity = 0

        for warehouse_dict in self.items.values():
            if warehouse and warehouse_dict.has_key(warehouse):
                quantity += warehouse_dict.get(warehouse).quantity
            elif warehouse is None:
                for item in warehouse_dict.values():
                    quantity += item.quantity

        return quantity

    def _reduce_quantity_for(self, order_id, warehouse, quantity):
        warehouses = self.items.get(order_id)
        item = warehouses.get(warehouse)

        if item.quantity == quantity:
            del warehouses[warehouse]
        else:
            item.quantity -= quantity

    def backorder_commitment(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.order_id, from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def revert(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.order_id, from_item.warehouse, from_item.quantity)
        to_state.track(to_item)



class BackorderState(TrackingState):

    class BackorderedItem(TrackingState.TrackingItem):
        """
        A backordered item is created when a product cannot be reserved.
        It tracks which order triggered its creation.
        """
        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.date = properties.get("date", None)
            self.order_id = properties.get("order_id", None)
            self.allocated = properties.get("allocated", 0)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
                (lambda i: i.date is not None),
                (lambda i: i.order_id is not None),
                (lambda i: i.allocated >= 0),
                ])


    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.BackorderedItem)
        self.items = {}

    def _track(self, item):
        if self.items.has_key(item.order_id):
            existing = self.items.get(item.order_id)
            item.quantity += existing.quantity
            item.allocated += existing.allocated
        self.items.update({ item.order_id: item })

    def get(self, order_id):
        return self.items.get(order_id, None)

    def quantity(self, order_id=None):
        if order_id:
            return 0 if not self.items.has_key(order_id) else self.items.get(order_id).quantity
        else:
            return reduce(operator.add, [item.quantity for item in self.items.values()], 0)

    def fulfill_backorder(self, to_state, from_item, to_item):
        item = self.items.get(from_item.order_id)

        # It completely fulfilled, backorder can be removed
        if item.quantity == from_item.allocated:
            del self.items[from_item.order_id]
        else:
            item.quantity -= from_item.allocated
            item.allocated -= from_item.allocated

        to_state.track(to_item)

    def cancel_backorder(self, to_state, from_item, to_item):
        del self.items[from_item.order_id]
        to_state.track(to_item)