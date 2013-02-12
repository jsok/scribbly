from mock import Mock, call
from unittest import TestCase, skip

from domain.service.delivery_service import DeliveryService
from domain.tests.factories.inventory import InventoryItemFactory
from domain.tests.factories.sales import OrderFactory


class DeliveryServiceTestCase(TestCase):

    def setUp(self):
        order1 = Mock()
        order1_line1 = Mock()
        order1_line1.sku = "PROD001"
        order1_line2 = Mock()
        order1_line2.sku = "PROD002"
        order1.line_items = Mock()
        order1.line_items.__iter__ = Mock(return_value=iter([order1_line1, order1_line2]))

        # order1 = OrderFactory.build(id="ORD001")
        # order1.add_line_item("PROD001", 1, 100.00, 0.10)
        # order1.add_line_item("PROD002", 3, 10.00, 0.00)

        order2 = Mock()
        order2_line1 = Mock()
        order2_line1.sku = "PROD001"
        order2_line2 = Mock()
        order2_line2.sku = "PROD002"
        order2.line_items = Mock()
        order2.line_items.__iter__ = Mock(return_value=iter([order2_line1, order2_line2]))

        # order2 = OrderFactory.build(id="ORD002")
        # order2.add_line_item("PROD001", 2, 100.00, 0.10)
        # order2.add_line_item("PROD002", 4, 10.00, 0.00)

        orders = {
            "ORD001": order1,
            "ORD002": order2,
        }

        self.order_repository = Mock()
        self.order_repository.find = Mock(side_effect=lambda order_id: orders.get(order_id))

        prod1 = InventoryItemFactory.build(sku="PROD001")
        prod1.enter_stock_on_hand(10, "WHSE001")
        prod1.enter_stock_on_hand(10, "WHSE002")
        prod1.commit(1, "WHSE001", "ORD001")
        prod1.commit(2, "WHSE002", "ORD002")

        prod2 = InventoryItemFactory.build(sku="PROD002")
        prod2.enter_stock_on_hand(10, "WHSE001")
        prod2.enter_stock_on_hand(10, "WHSE002")
        prod2.commit(3, "WHSE001", "ORD001")
        prod2.commit(2, "WHSE001", "ORD002")
        prod2.commit(2, "WHSE002", "ORD002")

        inventory = {
            "PROD001": prod1,
            "PROD002": prod2,
        }

        self.inventory_repository = Mock()
        self.inventory_repository.find = Mock(side_effect=lambda sku: inventory.get(sku))

    def test_generate_packing_list_from_order(self):
        service = DeliveryService(self.order_repository, self.inventory_repository)

        packing_list = service.generate_packing_list(["ORD001"])

        self.assertTrue(call("ORD001") in self.order_repository.find.call_args_list, "ORD001 was not queried for")
        self.assertTrue(call("PROD001") in self.inventory_repository.find.call_args_list, "PROD001 was not queried for")
        self.assertTrue(call("PROD002") in self.inventory_repository.find.call_args_list, "PROD002 was not queried for")

        for sku in ["PROD001", "PROD002"]:
            self.assertTrue(sku in packing_list.list_skus(), "Could not find {0} in SKU list".format(sku))
