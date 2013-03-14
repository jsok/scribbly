from mock import Mock
from unittest import TestCase, skip

from domain.model.pricing.discount import Discount
from domain.service.pricing_service import PricingService
from domain.service.ordering_service import OrderingService, OrderingError
from domain.tests.factories.customer import CustomerFactory
from domain.tests.factories.product import ProductFactory
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

        products = {
            "PROD001": ProductFactory.build(sku="PROD001", price_category="MANF-A"),
            "PROD002": ProductFactory.build(sku="PROD002", price_category="MANF-B"),
        }
        self.product_repository = Mock()
        self.product_repository.find = Mock(side_effect=lambda sku: products.get(sku))

        inv_prod1 = InventoryItemFactory.build(sku="PROD001")
        inv_prod1.enter_stock_on_hand(10)
        inv_prod1.enter_stock_on_hand(10)
        inv_prod1.commit(1, "ORD001")
        inv_prod1.commit(2, "ORD002")

        inv_prod2 = InventoryItemFactory.build(sku="PROD002")
        inv_prod2.enter_stock_on_hand(10)
        inv_prod2.enter_stock_on_hand(10)
        inv_prod2.commit(3, "ORD001")
        inv_prod2.commit(2, "ORD002")
        inv_prod2.commit(2, "ORD002")

        inventory = {
            "PROD001": inv_prod1,
            "PROD002": inv_prod2,
        }
        self.inventory_repository = Mock()
        self.inventory_repository.find = Mock(side_effect=lambda sku: inventory.get(sku))

        self.order_descriptors = {
            "ORD001": [
                {"sku": "PROD001", "quantity": 1, "warehouse": "WHSE001"},
                {"sku": "PROD002", "quantity": 3, "warehouse": "WHSE001"}
            ],
            "ORD002": [
                {"sku": "PROD001", "quantity": 2, "warehouse": "WHSE002"},
                {"sku": "PROD002", "quantity": 2, "warehouse": "WHSE001"},
                {"sku": "PROD002", "quantity": 2, "warehouse": "WHSE002"}
            ],
        }

    def test_order_bad_customer(self):
        service = OrderingService(self.customer_repository,
                                  self.product_repository,
                                  None,
                                  self.inventory_repository,
                                  self.pricing_service)

        with self.assertRaises(OrderingError):
            service.create_order("Fake Customer", None)