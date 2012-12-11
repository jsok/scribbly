import datetime

import factory

from domain.model.inventory import inventory_items, backordered_item, committed_item, purchase_ordered_item

class BackorderFactory(factory.Factory):
    FACTORY_FOR = backordered_item.BackOrderedItem

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    date = datetime.datetime.now()
    quantity = 1
    order_id = factory.Sequence(lambda n: 'ORD%03d'% n, type=int)

class CommitmentFactory(factory.Factory):
    FACTORY_FOR = committed_item.CommittedItem

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    date = datetime.datetime.now()
    quantity = 1
    order_id = factory.Sequence(lambda n: 'ORD%03d'% n, type=int)

class PurchaseOrderFactory(factory.Factory):
    FACTORY_FOR = purchase_ordered_item.PurchaseOrderedItem

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    date = datetime.datetime.now()
    quantity = 1
    purchase_order_id = factory.Sequence(lambda n: 'PO%03d'% n, type=int)
    eta_date = datetime.datetime.now() + datetime.timedelta(weeks=1)

class InventoryItemFactory(factory.Factory):
    FACTORY_FOR = inventory_items.InventoryItem

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    on_hand = 1
