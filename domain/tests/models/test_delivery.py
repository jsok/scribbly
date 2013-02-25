from unittest import TestCase, skip
from nose.tools import raises

from domain.tests.factories.delivery import DeliveryFactory


class DeliveryTestCase(TestCase):

    def test_delivery_items(self):
        delivery = DeliveryFactory.build()

        delivery.add_item("PROD001", 10, "WHSE001", "ORD001")
        delivery.add_item("PROD001", 5, "WHSE001", "ORD002")

        self.assertIsNotNone(delivery._find_item("PROD001", "WHSE001", "ORD001"), "Could not find PROD001")
        self.assertIsNotNone(delivery._find_item("PROD001", "WHSE001", "ORD002"), "Could not find PROD001")

        self.assertIsNone(delivery._find_item("PRODXXX", "WHSEXXX", "ORDXXX"), "Should not have found item")

        delivery.adjust_deliver_quantity("PROD001", 10, "WHSE001", "ORD001")
        delivery.adjust_deliver_quantity("PROD001", 2, "WHSE001", "ORD002")

        order_1 = delivery._find_item("PROD001", "WHSE001", "ORD001")
        order_2 = delivery._find_item("PROD001", "WHSE001", "ORD002")

        self.assertEquals(10, order_1.get("deliver_quantity"), "Wrong delivery qty set for ORD001")
        self.assertEquals(2, order_2.get("deliver_quantity"), "Wrong delivery qty set for ORD002")

    @raises(KeyError)
    def test_adjust_nonexistent_item(self):
        delivery = DeliveryFactory.build()
        delivery.adjust_deliver_quantity("PRODXXX", 0, "WHSEXXX", "ORDXXX")

    @raises(ValueError)
    def test_adjust_invalid_qty(self):
        delivery = DeliveryFactory.build()
        delivery.add_item("PROD001", 10, "WHSE001", "ORD001")
        delivery.adjust_deliver_quantity("PROD001", 11, "WHSE001", "ORD001")

    def test_get_delivery_orders(self):
        delivery = DeliveryFactory.build()

        delivery.add_item("PROD001", 10, "WHSE001", "ORD001")
        delivery.add_item("PROD001", 10, "WHSE002", "ORD001")
        delivery.add_item("PROD001", 5, "WHSE001", "ORD002")
        delivery.adjust_deliver_quantity("PROD001", 8, "WHSE001", "ORD001")
        delivery.adjust_deliver_quantity("PROD001", 10, "WHSE002", "ORD001")
        delivery.adjust_deliver_quantity("PROD001", 2, "WHSE001", "ORD002")

        for order_id, items in delivery.get_orders():
            for item in items:
                if order_id == "ORD001" and item["sku"] == "PROD001" and item["warehouse"] == "WHSE001":
                    self.assertEqual(8, item["quantity"], "Wrong qty for PROD001 in ORD001")
                if order_id == "ORD001" and item["sku"] == "PROD001" and item["warehouse"] == "WHSE002":
                    self.assertEqual(10, item["quantity"], "Wrong qty for PROD001 in ORD001")
                if order_id == "ORD002" and item["sku"] == "PROD001":
                    self.assertEqual(2, item["quantity"], "Wrong qty for PROD001 in ORD002")