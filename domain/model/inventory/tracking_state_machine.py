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
            raise StateValidationError("Provided state is not a TrackingState.")
        self.states.update({state.name: state})

    def transition(self, name, from_item_dict, to_item_dict, dry_run=None):
        """
        Retrieve the transition function and curry in the to_state.
        Validate the items being passed into each state.
        """
        if name not in self.transitions:
            raise TransitionValidationError("Unknown transition: {0}".format(name))
        from_state, to_state = self.transitions.get(name)

        from_item = from_state._validated_item(from_item_dict)
        if not from_item:
            raise TransitionValidationError("Could not validate {0}".format(from_item_dict))

        # Perform all pre-transition validations on initiating state
        transition = getattr(from_state, name)(from_item)
        validation_parameters = {}
        for validation in transition:
            if not validation.succeeded():
                raise TransitionValidationError(validation.message)
            else:
                validation_parameters = validation.parameters
                break  # Halt

        # Update any TransitionParameters with their values and validate to_item
        to_item = to_state._validated_item(to_item_dict, parameters=validation_parameters)
        if not to_item:
            raise TransitionValidationError("Could not validate {0}".format(to_item_dict))

        # Ensure receiving state is able to track item
        track = to_state._track(to_item)
        for validation in track:
            if not validation.succeeded():
                raise TransitionValidationError(validation.message)
            else:
                break  # Halt

        dry_run = True if dry_run else False
        if not dry_run:
            # Run to completion
            for validation in transition:
                pass
            for validation in track:
                pass

        return True

    def add_transition(self, name, from_state, to_state):
        """
        Add a transition between two states.
        The name is taken to be a method on the from_state.
        """
        from_state = self.states.get(from_state, None)
        to_state = self.states.get(to_state, None)

        for state in [from_state, to_state]:
            if not state:
                raise StateValidationError("State {0} does not exist.".format(state))

        if hasattr(from_state, name) and callable(getattr(from_state, name)):
            self.transitions.update({name: (from_state, to_state)})
        else:
            raise TransitionValidationError("State {0} does not define transition {1}".format(from_state, name))

    def action(self, name, args):
        """
        Perform an action which is limited in scope within the state.
        Args is a dict of arguments to pass to the action, validation is the responsibility of the state.
        """
        state = self.actions.get(name, None)
        if not state:  # pragma: no cover
            raise TransitionActionError("Unknown action: {0}".format(name))
        action = getattr(state, name)
        return functools.partial(action, args)

    def add_action(self, name, state):
        """
        Add an action to a state.
        The name is taken to be a method on the state.
        """
        state = self.states.get(state, None)
        if not state:
            raise StateValidationError("State {0} does not exist.".format(state))

        if hasattr(state, name):
            self.actions.update({name: state})
        else:
            raise TransitionActionError("State {0} does not define action {1}".format(state, name))


class StateValidationError(Exception):
    """
    An exception to indicate that the transition failed validation and will not be committed.
    """
    pass


class TransitionValidationError(Exception):
    """
    An exception to indicate that the transition failed validation and will not be committed.
    """
    pass


class TransitionActionError(Exception):
    """
    An exception to indicate that the action failed validation and will not be enacted.
    """
    pass


class TransitionParameter(object):
    """
    A Transition Parameter defines the communication protocol between the "from" state to the "to" state.
    The "to" state declares its unknown item parameters with a name which will be matched with any parameters
    emitted by the "from" state.
    The "to" state can optionally define a default value if the "from" state never emits the required parameter.
    If the "to" state does not define a default and no value is returned by the "from" state an exception will be
    raised and treated as a TransitionValidationError.
    The "from" state can use the same value argument to communicate back to the "to" state its value.
    """
    def __init__(self, name, value=None):
        self.name = name
        self.value = value if value else None


class TrackingState(object):
    class TrackingItem(object):
        def __init__(self):
            self.validations = []

        def validate(self):
            """
            Apply each rule to the item and only succeed if all validations pass.
            """
            return reduce(operator.and_, map(lambda f: f(self), self.validations), True)

        def export(self):
            """
            TrackingItems export themself to the world as a dict, so external consumers can determine their properties.
            """
            item_dict = self.__dict__.copy()
            item_dict.pop("validations")
            return item_dict

    class TransitionValidationResult(object):
        """
        The result of each validation step in a transition's action.
        If unsuccessful, the failure message can be checked for a reason.
        """
        def __init__(self, success, failure_message):
            self.success = success
            self.message = failure_message
            self.parameters = {}

        def succeeded(self):
            return self.success is True

        def add_parameter(self, name, value):
            self.parameters.update({name: value})

    def __init__(self, name, item_type):
        self.name = name
        self.item_type = item_type

    def _validated_item(self, item_dict, parameters=None):
        parameters = parameters if parameters else {}
        unvalidated_params = {v.name: k for k, v in item_dict.iteritems() if isinstance(v, TransitionParameter)}

        for name, value in parameters.iteritems():
            item_dict.update({unvalidated_params[name]: value})

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
        if not item:
            raise TransitionValidationError("Could not validate item {0} to track it.".format(item))

        for validation in self._track(item):
            if not validation.succeeded():
                raise TransitionValidationError(validation.message)

        return True

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

    def get(self, key):
        return self._get(key).export()

    def _get(self, key):
        """
        Internal get method to retrieve a tracked item by specified key.
        """
        raise NotImplementedError()  # pragma: no cover


class OnHandState(TrackingState):
    class OnHandItem(TrackingState.TrackingItem):
        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
            ])

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.OnHandItem)
        self.item = self.OnHandItem({"quantity": 0})

    def _track(self, item):
        yield self.TransitionValidationResult(True, None)
        self.item.quantity += item.quantity

    def quantity(self, key=None):
        return self.item.quantity

    def _reduce_quantity_by(self, quantity):
        current_quantity = self.item.quantity
        if quantity > current_quantity:
            yield self.TransitionValidationResult(False, "Cannot commit quantity greater than on hand")

        # Halt before committing transition
        yield self.TransitionValidationResult(True, None)
        self.item.quantity = max(0, current_quantity - quantity)

    def commit(self, item):
        return self._reduce_quantity_by(item.quantity)

    def allocate(self, item):
        return self._reduce_quantity_by(item.quantity)

    def lost(self, item):
        yield self.TransitionValidationResult(True, None)
        self.item.quantity = max(0, self.item.quantity - item.quantity)


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
            self.date = properties.get("date", datetime.datetime.now())
            self.order_id = properties.get("order_id", None)

            self.validations.extend([
                (lambda i: i.quantity > 0),
                (lambda i: i.unverified_quantity >= 0),
                (lambda i: i.date is not None),
                (lambda i: i.order_id is not None),
            ])

        def __repr__(self):
            return "{0} quantity={1} unverified_quantity={2} order_id={3}".format(
                self.__class__, self.quantity, self.unverified_quantity, self.order_id)

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.CommittedItem)
        self.items = {}
        # items is dict, keyed by order_id: { order_id: item }

    def _track(self, item):
        yield self.TransitionValidationResult(True, None)
        if item.order_id in self.items:
            self.items.get(item.order_id).quantity += item.quantity
        else:
            self.items[item.order_id] = item

    def _get(self, order_id):
        return self.items.get(order_id, None)

    def is_verified(self, order_id):
        for key, item in self.items.iteritems():
            if order_id in key and item.unverified_quantity > 0:
                return False
        return True

    def get_unverified(self):
        unverified_items = []

        for item in self.items.itervalues():
            if item.unverified_quantity > 0:
                unverified_items.append(item)

        return unverified_items

    def quantity(self, key=None):
        quantity = 0

        for item in self.items.itervalues():
            quantity += item.quantity
            quantity += item.unverified_quantity

        return quantity

    def _reduce_quantity_for(self, order_id, quantity):
        item = self.items.get(order_id, None)
        if not item:
            message = "Could not find commitment for {0}".format(order_id)
            yield self.TransitionValidationResult(False, message)

        if quantity > item.quantity:
            message = "Cannot commit {0} (maximum {1} for commitment for {2}".format(quantity, item.quantity, order_id)
            yield self.TransitionValidationResult(False, message)

        yield self.TransitionValidationResult(True, None)
        if item.quantity == quantity:
            del self.items[order_id]
        else:
            item.quantity -= quantity

    def backorder_commitment(self, item):
        return self._reduce_quantity_for(item.order_id, item.quantity)

    def revert(self, item):
        return self._reduce_quantity_for(item.order_id, item.quantity)

    def fulfill(self, item):
        return self._reduce_quantity_for(item.order_id, item.quantity)

    def verify(self, item):
        verified_quantity = item.get("quantity", None)
        if verified_quantity is None:
            raise KeyError()

        for item in self.items.itervalues():
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

    def verify_out_of_stock(self, verify_item):
        item = self.items.get(verify_item.order_id, None)
        if not item:
            message = "Could not find commitment for {0}".format(verify_item.order_id)
            yield self.TransitionValidationResult(False, message)

        yield self.TransitionValidationResult(True, None)
        item.unverified_quantity -= verify_item.quantity


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
        # Only allow tracking allocations if they already exist
        if item.allocated > 0 and item.order_id not in self.items:
            message = "Cannot allocate quantity {0} since backorder for order {1} does not exist".format(
                item.allocated, item.order_id)
            yield self.TransitionValidationResult(False, message)

        yield self.TransitionValidationResult(True, None)
        if item.order_id in self.items:
            existing = self.items.get(item.order_id)
            item.quantity += existing.quantity
            item.allocated += existing.allocated
        self.items.update({item.order_id: item})

    def _get(self, order_id):
        return self.items.get(order_id, None)

    def quantity(self, order_id=None):
        if order_id:
            return 0 if order_id not in self.items else self.items.get(order_id).quantity
        else:
            return reduce(operator.add, [item.quantity for item in self.items.values()], 0)

    def fulfill_backorder(self, item):
        backorder = self.items.get(item.order_id, None)
        if not backorder:
            message = "Could not find backorder for order {0}.".format(item.order_id)
            yield self.TransitionValidationResult(False, message)

        if item.quantity > backorder.quantity:
            message = "Cannot fulfill quantity {0}, greater than backorder quantity {1}.".format(
                item.quantity, backorder.quantity)
            yield self.TransitionValidationResult(False, message)

        yield self.TransitionValidationResult(True, None)
        # If completely fulfilled, backorder can be removed
        if backorder.quantity == item.allocated:
            del self.items[item.order_id]
        else:
            backorder.quantity -= item.allocated
            backorder.allocated -= item.allocated

    def cancel_backorder(self, item):
        if item.order_id not in self.items:
            message = "Cannot find order {0} in backorders.".format(item.order_id)
            yield self.TransitionValidationResult(False, message)

        success = self.TransitionValidationResult(True, None)
        # Return the allocated quantity which needs to be returned to On Hand state.
        success.add_parameter("allocated", item.allocated)
        yield success
        del self.items[item.order_id]


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
        if item.invoice_id in self.items:
            yield self.TransitionValidationResult(False, "Invoice {0} already exists.".format(item.invoice_id))

        yield self.TransitionValidationResult(True, None)
        self.items.update({item.invoice_id: item})

    def _get(self, invoice_id):
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
        if item.purchase_order_id in self.items:
            yield self.TransitionValidationResult(False, "Purchase {0} already exists.".format(item.purchase_order_id))

        yield self.TransitionValidationResult(True, None)
        self.items.update({item.purchase_order_id: item})

    def _get(self, purchase_order_id):
        return self.items.get(purchase_order_id, None)

    def quantity(self, purchase_order_id=None):
        if purchase_order_id:
            return 0 if purchase_order_id not in self.items else self.items.get(purchase_order_id).quantity
        else:
            return reduce(operator.add, [item.quantity for item in self.items.values()], 0)

    def delivery(self, item):
        purchase_order = self.items.get(item.purchase_order_id)
        if not purchase_order:
            message = "Could not find Purchase Order {0}.".format(item.purchase_order_id)
            yield self.TransitionValidationResult(False, message)

        yield self.TransitionValidationResult(True, None)
        if purchase_order.quantity == item.quantity:
            del self.items[purchase_order.purchase_order_id]
        else:
            purchase_order.quantity -= item.quantity

    def cancel_purchase_order(self, args):
        # We don't usually allow this, but there is no logical transition for it
        if "purchase_order_id" not in args:
            raise TransitionActionError("Purchase Order ID not specified.")
        self.items.pop(args["purchase_order_id"])


class LostAndFoundState(TrackingState):
    class LostAndFoundItem(TrackingState.TrackingItem):
        """
        Lost and Found items, due to mis-count or other mistake.
        """

        def __init__(self, properties):
            super(self.__class__, self).__init__()
            self.quantity = properties.get("quantity", 0)
            self.date = properties.get("date", None)

            self.validations.extend([
                (lambda i: i.quantity >= 0),
                (lambda i: i.date is not None),
            ])

    def __init__(self, name):
        super(self.__class__, self).__init__(name, self.LostAndFoundItem)
        self.items = []

    def _track(self, item):
        yield self.TransitionValidationResult(True, None)
        self.items.append(item)

    def quantity(self, key=None):
        return reduce(operator.add, [item.quantity for item in self.items], 0)

    def found(self, item):
        yield self.TransitionValidationResult(True, None)
        self.track(item)
