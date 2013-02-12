import datetime

from domain.shared.service import Service
from domain.model.sales.packing_list import PackingList


class DeliveryService(Service):
    """
    Domain service which creates deliveries and their documentation from orders.
    """

    def __init__(self, order_repository, inventory_repository):
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository

    def generate_packing_list(self, order_ids):
        packing_list = PackingList(None, datetime.datetime.now())

        for order_id in order_ids:
            order = self.order_repository.find(order_id)

            for line_item in order.line_items:
                inventory_item = self.inventory_repository.find(line_item.sku)
                print line_item.sku
                warehouses = inventory_item.find_committed_for_order(order_id)

                for item in warehouses.itervalues():
                    packing_list.add_item(line_item.sku, item.quantity, item.warehouse, item.order_id)

        return packing_list
