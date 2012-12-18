import datetime

import factory

from domain.model.sales import order, packing_list

class OrderFactory(factory.Factory):
    FACTORY_FOR = order.Order

    id = factory.Sequence(lambda n: 'ORD%03d'% n, type=int)
    order_date = datetime.datetime.now()

class PackingListFactory(factory.Factory):
    FACTORY_FOR = packing_list.PackingList

    id = factory.Sequence(lambda n: 'PACK%03d'% n, type=int)
    date = datetime.datetime.now()
    packer = "Employee 1"