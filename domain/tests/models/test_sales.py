from datetime import datetime
from unittest import TestCase, skip

from domain.tests.factories.sales import OrderFactory, PackingListFactory, InvoiceFactory


class SalesOrderTestCase(TestCase):
    def test_order_is_accepted(self):
        order = OrderFactory.build()

        self.assertIsNotNone(order.order_id, "Order ID was not set")
        self.assertIsNotNone(order.order_date, "Order date was not set")
        self.assertFalse(order.is_acknowledged(), "Order should not have been acknowledged")

        order.acknowledge(datetime.now())
        self.assertTrue(order.is_acknowledged(), "Order should not have been acknowledged")

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


class SalesInvoiceTestCase(TestCase):
    def test_invoice_is_accepted(self):
        invoice = InvoiceFactory.build()

        self.assertIsNotNone(invoice.invoice_id, "Invoice ID was not set")
        self.assertIsNotNone(invoice.invoice_date, "Invoice date was not set")
        self.assertFalse(invoice.finalised, "Invoice should not have been finalised")

    def test_invoice_adds_line_item(self):
        invoice = InvoiceFactory.build()
        invoice.add_line_item("PROD000", 1, 100.00, 0.10)

        self.assertEquals(1, len(invoice.line_items), "Line item was not added to Invoice correctly")
        self.assertEquals(90.00, invoice.total_amount(), "Incorrect order amount calculated")

    def test_invoice_with_varied_line_items(self):
        invoice = InvoiceFactory.build()
        invoice.add_line_item("PROD000", 1, 100.00, 0.10)
        invoice.add_line_item("PROD001", 1, 10.00, 0.00)

        self.assertEquals(2, len(invoice.line_items), "Both line items were not added correctly")
        self.assertEquals(100.00, invoice.total_amount(), "Incorrect invoice amount calculated")


    def test_invoice_with_single_tax_rate(self):
        invoice = InvoiceFactory.build()
        invoice.add_line_item("PROD000", 1, 100.00, 0.20, tax_rate=0.10)

        self.assertEquals(8.00, invoice.tax(), "Incorrect amount of tax calculated")
        self.assertEquals(80.00, invoice.subtotal(), "Incorrect subtotal calculated")
        self.assertEquals(88.00, invoice.total_amount(), "Incorrect total calculated")

    def test_invoice_with_multiple_tax_rates(self):
        invoice = InvoiceFactory.build()
        invoice.add_line_item("PROD000", 1, 100.00, 0.20, tax_rate=0.10)
        invoice.add_line_item("PROD001", 1, 10.00, 0.10, tax_rate=None)

        self.assertEquals(8.00, invoice.tax(), "Incorrect amount of tax calculated")
        self.assertEquals(89.00, invoice.subtotal(), "Incorrect subtotal calculated")
        self.assertEquals(97.00, invoice.total_amount(), "Incorrect total calculated")

    def test_invoice_with_invalid_discount_line_item(self):
        invoice = InvoiceFactory.build()
        invoice.add_line_item("PROD000", 1, 1.00, 2.0) # 200% discount

        self.assertEquals(0.0, invoice.total_amount(), "Invoice amount should be zero, not negative")
