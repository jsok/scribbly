from datetime import datetime
import operator

from domain.shared.service import Service
from domain.model.sales.order import Order


class OrderingService(Service):
    """
    A domain service which creates and manages orders.
    """

    def __init__(self, customer_repository, product_repository, order_repository, inventory_repository,
                 pricing_service):
        self.customer_repository = customer_repository
        self.product_repository = product_repository
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository
        self.pricing_service = pricing_service

    def create_order(self, customer, order_descriptors, customer_reference=None):
        """
        Creates an order for the given customer.
        1) Commits all items to inventory
        2) Auto-acknowledges order if not inventory verification required
        order_descriptor is a list of tuples: [ (sku, quantity) ]
        """
        customer_entity = self.customer_repository.find(customer)
        if not customer_entity:
            raise OrderingError("Cannot find specified customer for order")

        order = Order(self.order_repository.next_id(), customer, datetime.now(), customer_reference=customer_reference)
        self._add_order_line_items(order, customer_entity, order_descriptors)
        self._auto_acknowledge_order(order)

        customer_entity.submit_order(order.order_id)

        return order

    def _add_order_line_items(self, order, customer, order_descriptors):
        for sku, quantity in order_descriptors:
            product = self.product_repository.find(sku)
            if not product:
                raise OrderingError("Unknown product SKU: {0}".format(sku))

            discount = self.pricing_service.get_customer_discount(product, customer)

            order.add_line_item(sku, quantity, product.get_price(), discount)

    def _auto_acknowledge_order(self, order):
        """
        Acknowledge an order and commit its line items to the inventory.
        Acknowledgement fails if any inventory item needs verification.
        """

        inventory_commits = []
        inventory_verifications = []

        for line_item in order.line_items:
            inventory_item = self.inventory_repository.find(line_item.sku)
            if not inventory_item:
                message = "Cannot find Inventory Item for SKU={0}".format(line_item.sku)
                raise OrderingError(message)

            # Delay commit and verification of inventory item
            do_commit = lambda commit: inventory_item.commit(line_item.quantity, order.order_id, dry_run=not commit)
            inventory_commits.append(do_commit)

            needs_verify = lambda: inventory_item.needs_stock_verified(order.order_id)
            inventory_verifications.append(needs_verify)

        dry_run = map(lambda do_commit: do_commit(False), inventory_commits)
        commits_will_succeed = reduce(operator.and_, dry_run, True)

        # Inventory checks for all line items succeeded, proceed with commit
        if commits_will_succeed:
            map(lambda do_commit: do_commit(True), inventory_commits)
        else:
            raise OrderingError("Cannot commit all items in order to inventory")

        can_acknowledge = reduce(operator.and_,
                                 map(lambda verify: not verify(), inventory_verifications),
                                 True)
        if can_acknowledge:
            order.acknowledge(datetime.now())


class OrderingError(Exception):
    """
    A generic exception which is thrown when ordering fails.
    """
    pass