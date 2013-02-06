import datetime

from domain.model.sales.packing_list import PackingList

class DeliveryService(object):
    """
    Domain service which creates deliveries and their documentation from orders.
    """

    def generate_packing_list(self, orders):
        packing_list = PackingList(None, datetime.datetime.now())

        for order in orders:
            for item in order.line_items:
                packing_list.request_item(item.sku, item.quantity, order.id)

        return packing_list
