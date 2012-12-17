import datetime

import factory

from domain.model.sales import order

class OrderFactory(factory.Factory):
    FACTORY_FOR = order.Order

    id = factory.Sequence(lambda n: 'ORD%03d'% n, type=int)
    order_date = datetime.datetime.now()
