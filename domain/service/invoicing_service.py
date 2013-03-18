from datetime import datetime

from domain.shared.service import Service
from domain.model.sales.invoice import Invoice


class InvoicingService(Service):
    """
    A domain service which creates invoices from orders, but also indirectly via delivieries.
    """

    def __init__(self, customer_repository, invoice_repository, order_repository, inventory_repository,
                 tax_rate_repository):
        self.customer_repository = customer_repository
        self.invoice_repository = invoice_repository
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository
        self.tax_rate_repository = tax_rate_repository

    def _validate_order_descriptor(self, order_descriptor):
        for descriptor in order_descriptor:
            expected_keys = ("sku", "quantity")
            descriptor_keys = set(descriptor.keys())

            if not descriptor_keys.issubset(expected_keys):
                raise OrderDescriptorError("Invalid order descriptor: %s" % descriptor)

    def _invoice_order(self, order_id, descriptors=None):
        """
        Create an invoice for the given order ID.
        Optionally invoice only the items in the provided descriptor.
        Otherwise, entire order will be invoiced.

        An order descriptor has the format: [ { sku: X, quantity: Y }, ... ]
        """

        order = self.order_repository.find(order_id)
        if not order:
            raise InvoicingError("Cannot find Order with ID {0}".format(order_id))
        if not order.is_acknowledged():
            raise OrderUnacknowledgedError("Order {0} is not acknowledged".format(order_id))

        customer = self.customer_repository.find(order.customer)
        if not customer:
            raise InvoicingError("Cannot find customer {0} for delivery for order {1}".format(order.customer,
                                                                                          order.order_id))

        tax_rate = self.tax_rate_repository.find(customer.tax_category)

        invoice_id = self.invoice_repository.next_id()
        invoice = Invoice(invoice_id, order.customer, datetime.now(), order_id=order_id,
                          customer_reference=order.customer_reference)

        if not descriptors:
            descriptors = order.get_order_descriptor()
        else:
            self._validate_order_descriptor(descriptors)

        for descriptor in descriptors:
            sku = descriptor.get("sku")
            quantity = descriptor.get("quantity")

            inventory_item = self.inventory_repository.find(sku)
            if not inventory_item:
                raise InvoicingError("Could not find SKU %s in Inventory" % sku)

            commitment = inventory_item.find_committed_for_order(order_id)
            if not commitment:
                raise InvoicingError("Inventory commitment does not exist")

            if quantity > commitment["quantity"]:
                raise InvoicingError("Order descriptor has requested quantity greater than order commitment")

            for line_item in order.get_line_items_for_sku(sku):
                invoice.add_line_item(line_item.sku, quantity, line_item.price, line_item.discount,
                                      tax_rate=tax_rate.rate)

        return invoice

    def _finalise_invoice(self, invoice):
        for line_item in invoice.line_items:
            inventory_item = self.inventory_repository.find(line_item.sku)
            success = inventory_item.fulfill_commitment(line_item.quantity,
                                                        invoice.order_id,
                                                        invoice.invoice_id)
            if not success:
                message = "SKU={0} Quantity={1}, Order ID={2}, Invoice ID={3}".format(
                    line_item.sku,
                    line_item.quantity,
                    invoice.order_id,
                    invoice.invoice_id)
                raise InvoicingError("Could not fulfill commitment for: {0}".format(message))

    def invoice_delivery(self, delivery):
        order_descriptors = delivery.get_order_descriptors()

        invoices = []
        for order_id, descriptors in order_descriptors.iteritems():
            invoice = self._invoice_order(order_id, descriptors=descriptors)
            invoices.append(invoice)

        # Finalise
        for invoice in invoices:
            self._finalise_invoice(invoice)
        else:
            map(lambda invoice: delivery.add_invoice(invoice.invoice_id), invoices)

        return invoices

    def invoice_order(self, order_id):
        invoice = self._invoice_order(order_id)
        self._finalise_invoice(invoice)
        return invoice


class InvoicingError(Exception):
    """
    A generic exception which is thrown when invoicing fails.
    """
    pass


class OrderDescriptorError(Exception):
    """
    An order descriptor passed to the invoicing service does not validate.
    """
    pass


class OrderUnacknowledgedError(Exception):
    """
    An order which has not been acknowledged was attempted to be invoiced.
    """
    pass