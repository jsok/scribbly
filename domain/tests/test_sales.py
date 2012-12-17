from unittest import TestCase, skip

from factories.sales import OrderFactory

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
