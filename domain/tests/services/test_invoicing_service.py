from mock import Mock, call
from nose.tools import raises
from unittest import TestCase, skip

from domain.service.invoicing_service import InvoicingService
from domain.service.invoicing_service import InvoicingError, OrderUnacknowledgedError, OrderDescriptorError
from domain.tests.factories.customer import CustomerFactory
from domain.tests.factories.delivery import DeliveryFactory
from domain.tests.factories.inventory import InventoryItemFactory
from domain.tests.factories.sales import OrderFactory


class InvoicingServiceTestCase(TestCase):

    def setUp(self):
        customer = CustomerFactory.build(name="Customer")
        customer.orders = ["ORD001", "ORD002", "ORD00X"]

        self.customer_repository = Mock()
        self.customer_repository.find = Mock(return_value=customer)

        tax_rate = Mock()
        tax_rate.rate = 0.1
        self.tax_repository = Mock()
        self.tax_repository.find = Mock(return_value=tax_rate)

        order1 = OrderFactory.build(order_id="ORD001", customer_reference="CUST-PO001")
        order1.customer = "Customer"
        order1.add_line_item("PROD001", 1, 100.00, 0.10)
        order1.add_line_item("PROD002", 3, 10.00, 0.00)
        order1.is_acknowledged = Mock(return_value=True)

        order2 = OrderFactory.build(order_id="ORD002", customer_reference="CUST-PO002")
        order2.customer = "Customer"
        order2.add_line_item("PROD001", 2, 100.00, 0.10)
        order2.add_line_item("PROD002", 4, 10.00, 0.00)
        order2.is_acknowledged = Mock(return_value=True)

        order3 = OrderFactory.build(order_id="ORD003", customer_reference="CUST-PO003")
        order3.customer = "Customer"
        order3.add_line_item("PROD004", 1, 100.00, 0.10)
        order3.is_acknowledged = Mock(return_value=True)

        orderx = OrderFactory.build(order_id="ORD00X", customer_reference="CUST-PO00X")
        orderx.customer = "Fake Customer"
        orderx.is_acknowledged = Mock(return_value=False)

        self.orders = {
            "ORD001": order1,
            "ORD002": order2,
            "ORD003": order3,
            "ORD00X": orderx,  # An unacknowledged order with bad customer
        }

        self.order_repository = Mock()
        self.order_repository.find = Mock(side_effect=lambda order_id: self.orders.get(order_id))

        prod1 = InventoryItemFactory.build(sku="PROD001")
        prod1.enter_stock_on_hand(10)
        prod1.commit(1, "ORD001")
        prod1.commit(2, "ORD002")

        prod2 = InventoryItemFactory.build(sku="PROD002")
        prod2.enter_stock_on_hand(10)
        prod2.commit(3, "ORD001")
        prod2.commit(4, "ORD002")

        # Product with no commitments
        prod3 = InventoryItemFactory.build(sku="PROD003")
        prod3.enter_stock_on_hand(10)

        # Always failing commitment fulfillment
        prod4 = InventoryItemFactory.build(sku="PROD004")
        prod4.enter_stock_on_hand(10)
        prod4.commit(3, "ORD003")
        prod4.fulfill_commitment = Mock(side_effect=lambda x, y, z: False)

        inventory = {
            "PROD001": prod1,
            "PROD002": prod2,
            "PROD003": prod3,
            "PROD004": prod4,
        }

        self.inventory_repository = Mock()
        self.inventory_repository.find = Mock(side_effect=lambda sku: inventory.get(sku))

        self.invoice_repository = Mock()
        invoice_ids = ["INV002", "INV001"]
        self.invoice_repository.next_id = Mock(side_effect=lambda: invoice_ids.pop())

        self.order_descriptors = {
            "ORD001": [
                {"sku": "PROD001", "quantity": 1},
                {"sku": "PROD002", "quantity": 3}
            ],
            "ORD002": [
                {"sku": "PROD001", "quantity": 2},
                {"sku": "PROD002", "quantity": 2},
                {"sku": "PROD002", "quantity": 2}
            ],
            "ORD003": [
                {"sku": "PROD004", "quantity": 3},
            ],
            "ORD00X": [
                {"sku": "PROD001", "quantity": 1},
            ]
        }

    @raises(OrderDescriptorError)
    def test_invalid_order_descriptor(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)
        service._invoice_order("ORD001", [{"bad": None, "keys": None}])

    @raises(InvoicingError)
    def test_invoice_nonexistent_customer(self):
        customer_repository = Mock()
        customer_repository.find = Mock(return_value=None)

        self.orders["ORD00X"].is_acknowledged = Mock(return_value=True)

        service = InvoicingService(customer_repository, None, self.order_repository, None, None)
        service._invoice_order("ORD00X")

        self.assertTrue(call("Fake Customer") in self.customer_repository.find.call_args_list,
                        "Fake Customer was not queried for")

    @raises(InvoicingError)
    def test_invoice_order_no_such_order_id(self):
        service = InvoicingService(self.customer_repository, None, self.order_repository, None, None)

        service._invoice_order("ORDER-NONEXISTENT")

    @raises(OrderUnacknowledgedError)
    def test_invoice_unacknowledged_orders(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        service._invoice_order("ORD00X")

    @raises(InvoicingError)
    def test_invoice_descriptor_nonexistent_sku(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        self.order_descriptors["ORD001"][0]["sku"] = "PRODFAKE"
        service._invoice_order("ORD001", descriptors=self.order_descriptors["ORD001"])

        self.assertTrue(call("PRODFAKE") in self.inventory_repository.find.call_args_list, "SKU was not queried for")

    @raises(InvoicingError)
    def test_invoice_descriptor_nonexistent_commitment(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        # Order descriptor has a product with no corresponding commitment
        self.order_descriptors["ORD001"].append({"sku": "PROD003", "quantity": 10})

        service._invoice_order("ORD001", self.order_descriptors["ORD001"])

    @raises(InvoicingError)
    def test_invoice_descriptor_commitment_quantity_mismatch(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        # Order descriptor has a commitment for wrong quantity
        self.order_descriptors["ORD001"] = [{"sku": "PROD001", "quantity": 10}]

        service._invoice_order("ORD001", self.order_descriptors["ORD001"])

    def test_invoice_delivery(self):
        delivery = DeliveryFactory.build()
        delivery.add_item("PROD001", 1, "ORD001")
        delivery.add_item("PROD002", 3, "ORD001")
        delivery.add_item("PROD001", 2, "ORD002")
        delivery.add_item("PROD002", 4, "ORD002")
        delivery.adjust_deliver_quantity("PROD001", 1, "ORD001")
        delivery.adjust_deliver_quantity("PROD002", 3, "ORD001")
        delivery.adjust_deliver_quantity("PROD001", 2, "ORD002")
        delivery.adjust_deliver_quantity("PROD002", 4, "ORD002")

        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        invoices = service.invoice_delivery(delivery)

        self.assertEquals(2, len(invoices), "Exactly 2 invoices should have been created")

        inv_ord001 = [inv for inv in invoices if inv.order_id == "ORD001"][0]
        self.assertEquals("INV001", inv_ord001.invoice_id, "Wrong Invoice ID assigned")
        self.assertEquals("CUST-PO001", inv_ord001.customer_reference, "Incorrect customer reference")
        self.assertEquals(2, len(inv_ord001.line_items), "Invoice should only contain 2 line items")
        self.assertEquals(132.00, inv_ord001.total_amount(), "Invoice total is incorrect")
        self.assertFalse(inv_ord001.finalised, "Invoice should not yet be finalised")

        inv_ord002 = [inv for inv in invoices if inv.order_id == "ORD002"][0]
        self.assertEquals("INV002", inv_ord002.invoice_id, "Wrong Invoice ID assigned")
        self.assertEquals("CUST-PO002", inv_ord002.customer_reference, "Incorrect customer reference")
        self.assertEquals(2, len(inv_ord002.line_items), "Invoice should only contain 2 line items")
        self.assertEquals(242.00, inv_ord002.total_amount(), "Invoice total is incorrect")
        self.assertFalse(inv_ord002.finalised, "Invoice should not yet be finalised")

    def test_invoice_order(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        invoice = service.invoice_order("ORD001")

        self.assertEquals("INV001", invoice.invoice_id, "Wrong Invoice ID assigned")
        self.assertEquals("CUST-PO001", invoice.customer_reference, "Incorrect customer reference")
        self.assertEquals(2, len(invoice.line_items), "Invoice should only contain 2 line items")
        self.assertEquals(132.00, invoice.total_amount(), "Invoice total is incorrect")
        self.assertFalse(invoice.finalised, "Invoice should not yet be finalised")

    @raises(InvoicingError)
    def test_invoice_order_fulfill_commitment_fails(self):
        service = InvoicingService(self.customer_repository, self.invoice_repository, self.order_repository,
                                   self.inventory_repository, self.tax_repository)

        invoice = service.invoice_order("ORD003")