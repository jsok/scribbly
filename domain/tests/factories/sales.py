import datetime

import factory

from domain.model.sales import order, invoice


class OrderFactory(factory.Factory):
    FACTORY_FOR = order.Order

    order_id = factory.Sequence(lambda n: 'ORD%03d'% n, type=int)
    customer = "Customer Name"
    order_date = datetime.datetime.now()


class InvoiceFactory(factory.Factory):
    FACTORY_FOR = invoice.Invoice

    invoice_id = factory.Sequence(lambda n: 'INV%03d'% n, type=int)
    customer = "Customer Name"
    invoice_date = datetime.datetime.now()
