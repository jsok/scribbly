from mock import Mock, call
from unittest import TestCase, skip

from domain.model.pricing.discount import Discount
from domain.service.pricing_service import PricingService
from domain.service.ordering_service import OrderingService, OrderingError
from domain.tests.factories.customer import CustomerFactory
from domain.tests.factories.product import ProductFactory, PriceValueFactory
from domain.tests.factories.inventory import InventoryItemFactory


class OrderingServiceTestCase(TestCase):

    def setUp(self):
        self.discount_repository = Mock()
        self.discount_repository.find = Mock()
        discounts = {
            ("MANF-A", "GRADE-A"): Discount(0.3, "MANF-A", "GRADE-A"),
            ("MANF-B", "GRADE-A"): Discount(0.1, "MANF-B", "GRADE-A")
        }
        self.discount_repository.find = Mock(side_effect=lambda category, tier: discounts.get((category, tier)))
        self.pricing_service = PricingService(self.discount_repository)

        customers = {
            "Customer": CustomerFactory.build(name="Customer"),
        }
        self.customer_repository = Mock()
        self.customer_repository.find = Mock(side_effect=lambda sku: customers.get(sku))

        tax_rate = Mock()
        tax_rate.rate = 0.1
        self.tax_repository = Mock()
        self.tax_repository.find = Mock(return_value=tax_rate)

        prod1 = ProductFactory.build(sku="PROD001", price_category="MANF-A")
        prod1.set_price(PriceValueFactory.build(price=100.00))
        prod2 = ProductFactory.build(sku="PROD002", price_category="MANF-B")
        prod2.set_price(PriceValueFactory.build(price=20.00))
        self.products = {
            "PROD001": prod1,
            "PROD002": prod2,
        }
        self.product_repository = Mock()
        self.product_repository.find = Mock(side_effect=lambda sku: self.products.get(sku))

        inv_prod1 = InventoryItemFactory.build(sku="PROD001")
        inv_prod1.enter_stock_on_hand(10)

        inv_prod2 = InventoryItemFactory.build(sku="PROD002", on_hand_buffer=7)
        inv_prod2.enter_stock_on_hand(10)

        self.inventory = {
            "PROD001": inv_prod1,
            "PROD002": inv_prod2,
        }
        self.inventory_repository = Mock()
        self.inventory_repository.find = Mock(side_effect=lambda sku: self.inventory.get(sku))

        self.order_descriptors = {
            "ORD001": [
                ("PROD001", 1),
                ("PROD002", 3),
            ],
            "ORD002": [
                ("PROD001", 2),
                ("PROD002", 4),
            ]

        }

        self.order_repository = Mock()
        order_ids = ["ORD002", "ORD001"]
        self.order_repository.next_id = Mock(side_effect=lambda: order_ids.pop())

    def test_order_bad_customer(self):
        service = OrderingService(self.customer_repository,
                                  self.product_repository,
                                  self.order_repository,
                                  self.inventory_repository,
                                  self.pricing_service)

        with self.assertRaises(OrderingError):
            service.create_order("Fake Customer", None)

        self.assertTrue(call("Fake Customer") in self.customer_repository.find.call_args_list,
                        "Fake Customer was not queried for")

    def test_order_bad_product(self):
        service = OrderingService(self.customer_repository,
                                  self.product_repository,
                                  self.order_repository,
                                  self.inventory_repository,
                                  self.pricing_service)

        order_descriptors = [
            ("PROD001", 1),
            ("PROD-FAKE", 1),
        ]

        with self.assertRaises(OrderingError):
            service.create_order("Customer", order_descriptors)

        self.assertTrue(call("PROD-FAKE") in self.product_repository.find.call_args_list,
                        "Fake product was not queried for")

    def test_order_creation(self):
        service = OrderingService(self.customer_repository,
                                  self.product_repository,
                                  self.order_repository,
                                  self.inventory_repository,
                                  self.pricing_service)

        order = service.create_order("Customer", self.order_descriptors["ORD001"], customer_reference="Customer-PO-Ref")

        self.assertEquals("Customer-PO-Ref", order.customer_reference, "Customer reference not set correctly")
        self.assertTrue(order.is_acknowledged(), "Order should not have been acknowledged")
        self.assertEquals("ORD001", order.order_id, "Order ID was not set correctly")

        for line_item in order.line_items:
            if line_item.sku == "PROD001":
                self.assertTrue(call("PROD001") in self.product_repository.find.call_args_list,
                                "Product PROD001 was not queried for")
                self.assertEquals(1, line_item.quantity, "Incorrect Quantity for PROD001")
                self.assertEquals(100.00, line_item.price, "Incorrect price for PROD001")
                self.assertEquals(0.3, line_item.discount, "Incorrect discount for PROD001")
            if line_item.sku == "PROD002":
                self.assertTrue(call("PROD002") in self.product_repository.find.call_args_list,
                                "Product PROD002 was not queried for")
                self.assertEquals(3, line_item.quantity, "Incorrect Quantity for PROD002")
                self.assertEquals(20.00, line_item.price, "Incorrect price for PROD002")
                self.assertEquals(0.1, line_item.discount, "Incorrect discount for PROD002")
            else:
                self.assert_("Unknown item found in order")

    def test_order_fails_no_inventory_item(self):
        service = OrderingService(self.customer_repository,
                                  self.product_repository,
                                  self.order_repository,
                                  self.inventory_repository,
                                  self.pricing_service)

        # Remove PROD002 from inventory
        self.inventory.pop("PROD002")

        with self.assertRaises(OrderingError):
            order = service.create_order("Customer", self.order_descriptors["ORD001"])

        self.assertTrue(call("PROD002") in self.product_repository.find.call_args_list,
                        "Product PROD002 was not queried for")
        self.assertTrue(call("PROD002") in self.inventory_repository.find.call_args_list,
                        "Product PROD002 was not queried for")

    def test_order_cannot_auto_acknowledge(self):
        service = OrderingService(self.customer_repository,
                                  self.product_repository,
                                  self.order_repository,
                                  self.inventory_repository,
                                  self.pricing_service)

        # PROD002 has a high on hand buffer, ORD002 should trigger a verification requirement and thus
        # not auto-acknowledge
        order = service.create_order("Customer", self.order_descriptors["ORD002"])

        self.assertFalse(order.is_acknowledged(), "Order should not have been acknowledged")

        # Rest of the order should be fine however
        for line_item in order.line_items:
            if line_item.sku == "PROD001":
                self.assertEquals(2, line_item.quantity, "Incorrect Quantity for PROD001")
                self.assertEquals(100.00, line_item.price, "Incorrect price for PROD001")
                self.assertEquals(0.3, line_item.discount, "Incorrect discount for PROD001")
            if line_item.sku == "PROD002":
                self.assertEquals(4, line_item.quantity, "Incorrect Quantity for PROD002")
                self.assertEquals(20.00, line_item.price, "Incorrect price for PROD002")
                self.assertEquals(0.1, line_item.discount, "Incorrect discount for PROD002")
            else:
                self.assert_("Unknown item found in order")
