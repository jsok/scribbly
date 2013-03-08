import functools
import operator


class TrackingStateMachine(object):
    def __init__(self):
        self.states = {}
        self.transitions = {}
        self.actions = {}

    def state(self, name):
        return self.states.get(name, None)

    def add_state(self, state):
        if not isinstance(state, TrackingState):
            raise TypeError()
        self.states.update({state.name: state})

    def transition(self, name, from_item_dict, to_item_dict):
        """
        Retrieve the transition function and curry in the to_state.
        Validate the items being passed into each state.
        """
        null_op = lambda: None
        if name not in self.transitions:
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
            self.transitions.update({name: (from_state, to_state)})
        else:
            raise ValueError()

    def action(self, name, args):
        """
        Perform an action which is limited in scope within the state.
        Args is a dict of arguments to pass to the action, validation is the responsibility of the state.
        """
        state = self.actions.get(name, None)
        if not state:  # pragma: no cover
            return lambda: None
        action = getattr(state, name)
        return functools.partial(action, args)

    def add_action(self, name, state):
        """
        Add an action to a state.
        The name is taken to be a method on the state.
        """
        state = self.states.get(state, None)
        if not state:
            raise ValueError()

        if hasattr(state, name):
            self.actions.update({name: state})
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
        raise NotImplementedError()  # pragma: no cover

    def quantity(self, key=None):
        """
        Quantity of items tracked, most implementors will have additional keys to filter on.
        """
        raise NotImplementedError()  # pragma: no cover


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
        self.items.update({item.warehouse: new_quantity})

    def quantity(self, warehouse=None):
        if warehouse:
            return self.items.get(warehouse, 0)
        else:
            return reduce(operator.add, [qty for qty in self.items.values()], 0)

    def _reduce_quantity_for(self, warehouse, quantity):
        current_quantity = self.items.get(warehouse)
        self.items.update({warehouse: max(0, current_quantity - quantity)})

    def commit(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def allocate(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def lost(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.warehouse, from_item.quantity)
        to_state.track(to_item)


class CommittedState(TrackingState):
    class CommittedItem(TrackingState.TrackingItem):
        """
        When an order is acknowledged, it will commit items from the inventory.
        A committed item affects on-hand count and will eventually be shipped.
        As a safe-guard, a quantity can be marked as unverified until a physical count can confirm its existence.
        """

        def __init__(self, properties):
            import datetime

            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.unverified_quantity = properties.get("unverified_quantity", 0)
            self.warehouse = properties.get("warehouse", None)
            self.date = properties.get("date", datetime.datetime.now())
            self.order_id = properties.get("order_id", None)

            self.validations.extend([
                (lambda i: i.quantity > 0),
                (lambda i: i.unverified_quantity >= 0),
                (lambda i: i.warehouse is not None),
                (lambda i: i.date is not None),
                (lambda i: i.order_id is not None),
            ])

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.CommittedItem)
        self.items = {}
        # items is dict, keyed by (order_id, warehouse) tuple: { (order_id, warehouse): item }

    def _track(self, item):
        if (item.order_id, item.warehouse) in self.items:
            self.items.get((item.order_id, item.warehouse)).update(item)
        else:
            self.items[(item.order_id, item.warehouse)] = item

    def get(self, order_id):
        matches = {}
        for key, item in self.items.iteritems():
            if order_id in key:
                matches[key] = item

        return matches

    def get_unverified(self, warehouse):
        unverified_items = []

        for key, item in self.items.iteritems():
            if warehouse in key and item.unverified_quantity > 0:
                unverified_items.append(item)

        return unverified_items

    def quantity(self, warehouse=None):
        quantity = 0

        for item in self.items.itervalues():
            if warehouse and item.warehouse != warehouse:
                continue
            else:
                quantity += item.quantity
                quantity += item.unverified_quantity

        return quantity

    def _reduce_quantity_for(self, order_id, warehouse, quantity):
        item = self.items.get((order_id, warehouse), None)

        if item.quantity == quantity:
            del self.items[(order_id, warehouse)]
        else:
            item.quantity -= quantity

    def backorder_commitment(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.order_id, from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def revert(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.order_id, from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def fulfill(self, to_state, from_item, to_item):
        self._reduce_quantity_for(from_item.order_id, from_item.warehouse, from_item.quantity)
        to_state.track(to_item)

    def verify(self, item):
        verified_quantity = item.get("quantity", None)
        if verified_quantity is None:
            raise KeyError()

        warehouse = item["warehouse"]
        for item in [v for k,v in self.items.iteritems() if warehouse in k]:
            # TODO: Verify oldest orders first

            if item.quantity <= verified_quantity:
                verified_quantity -= item.quantity

                if item.unverified_quantity <= verified_quantity:
                    verified_quantity -= item.unverified_quantity
                    item.quantity += item.unverified_quantity
                    item.unverified_quantity = 0
                else:
                    verified_quantity = 0

            else:
                # Move falsely committed quantity to unverified
                item.unverified_quantity += max(0, item.quantity - verified_quantity)
                item.quantity = verified_quantity
                verified_quantity = 0

    def verify_out_of_stock(self, to_state, from_item, to_item):
        item = self.items.get((from_item.order_id, from_item.warehouse))
        item.unverified_quantity -= from_item.quantity

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
        self.items.update({item.order_id: item})

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


class FulfilledState(TrackingState):
    class FulfilledItem(TrackingState.TrackingItem):
        """
        A fulfilled item has been removed from the warehouse and sent to a customer as part of a delivery.
        This item tracks when it was fulfilled and how.
        """

        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.date = properties.get("date", None)
            self.order_id = properties.get("order_id", None)
            self.invoice_id = properties.get("invoice_id", None)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
                (lambda i: i.date is not None),
                (lambda i: i.order_id is not None),
                (lambda i: i.invoice_id is not None),
            ])

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.FulfilledItem)
        self.items = {}

    def _track(self, item):
        # Invoices are immutable once entered
        if item.invoice_id in self.items:  # pragma: no cover
            return

        self.items.update({item.invoice_id: item})

    def get(self, invoice_id):
        return self.items.get(invoice_id, None)

    def quantity(self, invoice_id=None):
        if invoice_id:
            return 0 if invoice_id not in self.items else self.items.get(invoice_id).quantity
        else:
            return reduce(operator.add, [item.quantity for item in self.items.values()], 0)


class PurchaseOrderState(TrackingState):
    class PurchasedItem(TrackingState.TrackingItem):
        """
        When an purchase order for an item is issued to a supplier we track it.
        This item tracks when it was issue and when we expect it.
        """

        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.date = properties.get("date", None)
            self.eta_date = properties.get("eta_date", None)
            self.purchase_order_id = properties.get("purchase_order_id", None)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
                (lambda i: i.date is not None),
                (lambda i: i.purchase_order_id is not None),
            ])

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.PurchasedItem)
        self.items = {}

    def _track(self, item):
        # Purchase Orders are immutable once entered
        if item.purchase_order_id in self.items: # pragma: no cover
            return

        self.items.update({item.purchase_order_id: item})

    def get(self, purchase_order_id):
        return self.items.get(purchase_order_id, None)

    def quantity(self, purchase_order_id=None):
        if purchase_order_id:
            return 0 if purchase_order_id not in self.items else self.items.get(purchase_order_id).quantity
        else:
            return reduce(operator.add, [item.quantity for item in self.items.values()], 0)

    def delivery(self, to_state, from_item, to_item):
        item = self.items.get(from_item.purchase_order_id)

        if item.quantity == from_item.quantity:
            del self.items[item.purchase_order_id]
        else:
            item.quantity -= from_item.quantity

        to_state.track(to_item)

    def cancel_purchase_order(self, args):
        # We don't usually allow this, but there is no logical transition for it
        if "purchase_order_id" not in args:
            return
        self.items.pop(args["purchase_order_id"])


class LostAndFoundState(TrackingState):
    class LostAndFoundItem(TrackingState.TrackingItem):
        """
        Lost and Found items, due to mis-count or other mistake.
        """

        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.warehouse = properties.get("warehouse", None)
            self.date = properties.get("date", None)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
                (lambda i: i.warehouse is not None),
                (lambda i: i.date is not None),
            ])

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.LostAndFoundItem)
        self.items = []

    def _track(self, item):
        self.items.append(item)

    def quantity(self, warehouse=None):
        if warehouse:
            return reduce(operator.add, [item.quantity for item in self.items if item.warehouse == warehouse], 0)
        else:
            return reduce(operator.add, [item.quantity for item in self.items], 0)

    def found(self, to_state, from_item, to_item):
        self.track(from_item)
        to_state.track(to_item)
