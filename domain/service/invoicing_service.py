from datetime import datetime
import operator

from domain.shared.service import Service
from domain.model.sales.invoice import Invoice


class InvoicingService(Service):
    """
    A domain service which creates invoices from orders, but also indirectly via delivieries.
    """

    def __init__(self, customer_repository, order_repository, inventory_repository, tax_rate_repository):
        self.customer_repository = customer_repository
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository
        self.tax_rate_repository = tax_rate_repository

    def _validate_order_descriptor(self, order_descriptor):
        for descriptor in order_descriptor:
            expected_keys = ("sku", "quantity", "warehouse")
            descriptor_keys = set(descriptor.keys())

            if not descriptor_keys.issubset(expected_keys):
                raise OrderDescriptorError("Invalid order descriptor: %s" % descriptor)

    def _invoice_order_descriptors(self, customer_id, order_descriptors):
        """
        An order descriptor is a subset of line items which need to be invoiced.

        Format:
        { ORDER_ID: [{ sku: X, quantity: Y, warehouse: Z }, ], }

        If ORDER_ID is None, this is an ad-hoc invoice (i.e. no originating order document).

        Process:
         1) Verify customer and ensure all orders belong to them
         2) Retrieve customer's applicable tax rate
         3) Create an invoice per unique order
          a) Verify order line item against inventory commitments
          b) Copy line item to invoice
         4) Finalise invoice and update inventory
        """

        map(lambda desc: self._validate_order_descriptor(desc), order_descriptors.itervalues())

        customer = self.customer_repository.find(customer_id)
        if not customer:
            raise ValueError("Cannot find specified customer for delivery")

        if False in map(lambda order_id: order_id in customer.orders, order_descriptors.keys()):
            raise InvoicingError("All orders must belong to the same customer")

        tax_rate = self.tax_rate_repository.find(customer.tax_category)

        invoices = []
        for order_id, descriptors in order_descriptors.iteritems():
            order = self.order_repository.find(order_id)

            if not order.is_acknowledged():
                raise OrderUnacknowledgedError

            invoice = Invoice(None, customer_id, datetime.now(), order_id=order_id,
                              customer_reference=order.customer_reference)

            for descriptor in descriptors:
                sku = descriptor.get("sku")
                warehouse = descriptor.get("warehouse")
                quantity = descriptor.get("quantity")

                inventory_item = self.inventory_repository.find(sku)
                if not inventory_item:
                    raise InvoicingError("Could not find SKU %s in Inventory" % sku)

                warehouses = inventory_item.find_committed_for_order(order_id)
                commitment = warehouses.get(warehouse, None)
                if not commitment:
                    raise InvoicingError("Inventory commitment does not exist")

                if quantity > commitment.quantity:
                    raise InvoicingError("Order descriptor has requested quantity greater than order commitment")

                for line_item in order.get_line_items_for_sku(sku):
                    invoice.add_line_item(line_item.sku, quantity, line_item.price, line_item.discount,
                                          tax_rate=tax_rate.rate)

            if invoice.line_items:
                invoices.append(invoice)

        return invoices


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