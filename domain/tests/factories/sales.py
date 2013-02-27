import datetime

import factory

from domain.model.sales import order, packing_list, invoice


class OrderFactory(factory.Factory):
    FACTORY_FOR = order.Order

    order_id = factory.Sequence(lambda n: 'ORD%03d'% n, type=int)
    customer = "Customer Name"
    order_date = datetime.datetime.now()


class PackingListFactory(factory.Factory):
    FACTORY_FOR = packing_list.PackingList

    packinglist_id = factory.Sequence(lambda n: 'PACK%03d'% n, type=int)
    date = datetime.datetime.now()
    packer = "Employee 1"


class InvoiceFactory(factory.Factory):
    FACTORY_FOR = invoice.Invoice

    invoice_id = factory.Sequence(lambda n: 'INV%03d'% n, type=int)
    customer = "Customer Name"
    invoice_date = datetime.datetime.now()
