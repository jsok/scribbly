from unittest import TestCase, skip

from factories.sales import OrderFactory, PackingListFactory

class SalesOrderTestCase(TestCase):

    def test_order_is_accepted(self):
        order = OrderFactory.build()

        self.assertIsNotNone(order.id, "Order ID was not set")
        self.assertIsNotNone(order.order_date, "Order date was not set")
        self.assertFalse(order.is_acknowledged(), "Order should not have been acknowledged")

    def test_order_adds_line_item(self):
        order = OrderFactory.build()
        order.add_line_item("PROD000", 1, 100.00, 0.10)

        self.assertEquals(1, len(order.line_items), "Line item was not added to order correctly")
        self.assertEquals(90.00, order.total_amount(), "Incorrect order amount calculated")

    def test_order_with_varied_line_items(self):
        order = OrderFactory.build()
        order.add_line_item("PROD000", 1, 100.00, 0.10)
        order.add_line_item("PROD001", 1, 10.00, 0.00)

        self.assertEquals(2, len(order.line_items), "Both line items were not added correctly")
        self.assertEquals(100.00, order.total_amount(), "Incorrect order amount calculated")

    def test_order_with_invalid_discount_line_item(self):
        order = OrderFactory.build()
        order.add_line_item("PROD000", 1, 1.00, 2.0) # 200% discount

        self.assertEquals(0.0, order.total_amount(), "Order amount should be zero, not negative")

class PackingListTestCase(TestCase):

    def test_packing_list_empty(self):
        pl = PackingListFactory.build()
        self.assertIsNone(pl.find_item("PROD000"), "Packing list should have been empty")

    def test_packing_list_add_item(self):
        pl = PackingListFactory.build()
        pl.add_item("PROD000", 1, "ORD000")

        product = pl.find_item("PROD000")
        self.assertEquals(1, product.quantity, "Incorrect number of items for product in packing list")

    def test_packing_list_item_from_multiple_orders(self):
        pl = PackingListFactory.build()
        pl.add_item("PROD000", 1, "ORD000")
        pl.add_item("PROD000", 1, "ORD001")
        pl.add_item("PROD001", 3, "ORD000")
        pl.add_item("PROD002", 7, "ORD002")

        self.assertEquals(2, pl.find_item("PROD000").quantity,
            "Incorrect number of items for product in packing list")
        self.assertEquals(3, pl.find_item("PROD001").quantity,
            "Incorrect number of items for product in packing list")
        self.assertEquals(7, pl.find_item("PROD002").quantity,
            "Incorrect number of items for product in packing list")