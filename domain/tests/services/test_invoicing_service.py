from mock import Mock, call
from nose.tools import raises
from unittest import TestCase, skip

from domain.service.invoicing_service import InvoicingService
from domain.tests.factories.customer import CustomerFactory
from domain.tests.factories.inventory import InventoryItemFactory
from domain.tests.factories.sales import OrderFactory


class InvoicingServiceTestCase(TestCase):

    def setUp(self):
        customer = CustomerFactory.build(name="Customer")
        customer.orders = ["ORD001", "ORD002", "ORD00X"]

        self.customer_repository = Mock()
        self.customer_repository.find = Mock(return_value=customer)

        tax_rate = Mock()
        tax_rate.rate = Mock(side_effect=0.1)
        self.tax_repository = Mock()
        self.tax_repository.find = Mock(return_value=tax_rate)

        order1 = OrderFactory.build(order_id="ORD001", customer_reference="CUST-PO001")
        order1.add_line_item("PROD001", 1, 100.00, 0.10)
        order1.add_line_item("PROD002", 3, 10.00, 0.00)
        order1.is_acknowledged = Mock(return_value=True)

        order2 = OrderFactory.build(order_id="ORD002", customer_reference="CUST-PO002")
        order2.add_line_item("PROD001", 2, 100.00, 0.10)
        order2.add_line_item("PROD002", 4, 10.00, 0.00)
        order2.is_acknowledged = Mock(return_value=True)

        orderx = OrderFactory.build(order_id="ORD00X", customer_reference="CUST-PO00X")
        orderx.is_acknowledged = Mock(return_value=False)

        orders = {
            "ORD001": order1,
            "ORD002": order2,
            "ORD00X": orderx,  # An unacknowledged order
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

    @raises(ValueError)
    def test_invalid_order_descriptor(self):
        service = InvoicingService(None, None, None, None)
        service.invoice_order_descriptors("Customer", {
            "ORD001": [{"bad": None, "keys": None}]
        })

    @raises(ValueError)
    def test_invoice_nonexistent_customer(self):
        customer_repository = Mock()
        customer_repository.find = Mock(return_value=None)

        service = InvoicingService(customer_repository, None, None, None)
        service.invoice_order_descriptors("Fake Customer", {})

    @raises(LookupError)
    def test_invoice_orders_from_multiple_customers(self):
        service = InvoicingService(self.customer_repository, None, None, None)

        self.order_descriptors["ORD999"] = []  # Does not belong to Customer

        service.invoice_order_descriptors("Customer", self.order_descriptors)

    @raises(StandardError)
    def test_invoice_unacknowledged_orders(self):
        service = InvoicingService(self.customer_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        self.order_descriptors["ORD00X"] = []  # Has not been acknowledged

        service.invoice_order_descriptors("Customer", self.order_descriptors)

    @raises(LookupError)
    def test_invoice_descriptor_nonexistent_sku(self):
        service = InvoicingService(self.customer_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        # Order descriptor has a quantity greater than the order's commitment in the inventory
        self.order_descriptors["ORD001"][0]["sku"] = "PRODFAKE"
        print self.order_descriptors

        service.invoice_order_descriptors("Customer", self.order_descriptors)

    @ raises(ValueError)
    def test_invoice_descriptor_inventory_mismatch(self):
        service = InvoicingService(self.customer_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        # Order descriptor has a quantity greater than the order's commitment in the inventory
        self.order_descriptors["ORD001"][0]["quantity"] = 10
        print self.order_descriptors

        service.invoice_order_descriptors("Customer", self.order_descriptors)
