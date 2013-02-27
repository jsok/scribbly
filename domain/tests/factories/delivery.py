import datetime
import factory

from domain.model.delivery.delivery import Delivery


class DeliveryFactory(factory.Factory):
    FACTORY_FOR = Delivery

    delivery_id = factory.Sequence(lambda n: 'DELIVERY%03d'% n, type=int)
    customer = "Customer Name"
    date = datetime.datetime.now()