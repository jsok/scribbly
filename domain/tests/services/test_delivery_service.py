from unittest import TestCase, skip

from domain.service.delivery_service import DeliveryService
from domain.tests.factories.sales import OrderFactory, PackingListFactory

class DeliveryServiceTestCase(TestCase):

    def test_generate_packing_list_from_order(self):
        service = DeliveryService()

        order = OrderFactory.build()
        order.add_line_item("PROD000", 1, 100.00, 0.10)
        order.add_line_item("PROD001", 2, 10.00, 0.00)

        packing_list = service.generate_packing_list([order])

        self.assertEquals(1, packing_list.find_item("PROD000").quantity_requested, "PROD000 not found in packing list")
        self.assertEquals(2, packing_list.find_item("PROD001").quantity_requested, "PROD001 not found in packing list")

    def test_generate_packing_list_from_multiple_orders(self):
        service = DeliveryService()

        orders = [OrderFactory.build() for _ in range(3)]
        orders[0].add_line_item("PROD000", 1, 100.00, 0.10)
        orders[0].add_line_item("PROD001", 1, 10.00, 0.00)
        orders[1].add_line_item("PROD000", 2, 100.00, 0.10)
        orders[1].add_line_item("PROD001", 2, 10.00, 0.00)
        orders[2].add_line_item("PROD000", 3, 100.00, 0.10)
        orders[2].add_line_item("PROD001", 3, 10.00, 0.00)

        packing_list = service.generate_packing_list(orders)

        self.assertEquals(6, packing_list.find_item("PROD000").quantity_requested, "PROD000 not found in packing list")
        self.assertEquals(6, packing_list.find_item("PROD001").quantity_requested, "PROD001 not found in packing list")
