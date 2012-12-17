from unittest import TestCase, skip

from factories.sales import OrderFactory

class SalesOrderTestCase(TestCase):

    def test_order_is_accepted(self):
        order = OrderFactory.build()

        self.assertIsNotNone(order.id, "Order ID was not set")
        self.assertIsNotNone(order.order_date, "Order date was not set")
        self.assertFalse(order.is_acknowledged(), "Order should not have been acknowledged")