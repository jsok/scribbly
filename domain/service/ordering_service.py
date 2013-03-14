from datetime import datetime

from domain.shared.service import Service
from domain.model.sales.order import Order


class OrderingService(Service):
    def __init__(self, customer_repository, product_repository, order_repository, inventory_repository,
                 pricing_service):
        self.customer_repository = customer_repository
        self.product_repository = product_repository
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository
        self.pricing_service = pricing_service

    def create_order(self, customer, order_descriptors, customer_reference=None):
        """
        Creates an unacknowledged order for the given customer.
        order_descriptor is a list of tuples: [ (sku, quantity) ]
        """
        customer_entity = self.customer_repository.find(customer)
        if not customer_entity:
            raise OrderingError("Cannot find specified customer for order")

        order = Order(None, customer, datetime.now(), customer_reference=customer_reference)
        self._add_order_line_items(order, customer_entity, order_descriptors)

        # XXX: Order ID not yet allocated
        customer_entity.submit_order(order.order_id)

        return order

    def _add_order_line_items(self, order, customer, order_descriptors):
        for sku, quantity in order_descriptors:
            product = self.product_repository.find(sku)
            if not product:
                raise OrderingError("Unknown product SKU: {0}".format(sku))

            discount = self.pricing_service.get_customer_discount(product, customer)

            order.add_line_item(sku, quantity, product.get_price(), discount)

    def acknowledge_order(self, order, location_descriptor):
        """
        Acknowledge an order and commit its line items to the inventory.
        location_descriptors is a dict: {sku: [(warehouse, quantity)]}
        """

        # Ensure there exists location descriptors for all line items
        order_skus = set([line_item.sku for line_item in order.line_items])
        location_skus = set(location_descriptor.iterkeys())

        if not order_skus.issubset(location_skus):
            missing_skus = order_skus.difference(location_skus).intersection(order_skus)
            message = "Cannot acknowledge order. Missing SKU locations for: {0}".format(missing_skus)
            raise OrderingError(message)

        inventory_commits = []
        for line_item in order.line_items:
            inventory_item = self.inventory_repository.find(line_item.sku)
            if not inventory_item:
                message = "Cannot find Inventory Item for SKU={0}".format(line_item.sku)
                raise OrderingError(message)

            locations = location_descriptor.get(line_item.sku)

            for warehouse, quantity in locations:
                # Do not perform commit, store lambda for later execution
                do_commit = lambda: inventory_item.commit(quantity, order.order_id)
                inventory_commits.append(do_commit)

        # Inventory checks for all line items succeeded, proceed with commit
        for commit in inventory_commits:
            commit()

        order.acknowledge(datetime.now())
        return True


class OrderingError(Exception):
    """
    A generic exception which is thrown when ordering fails.
    """
    pass