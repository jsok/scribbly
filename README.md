Scribbly ERP
============

Installation
------------

Create virtualenv:
```
# virtualenv virtualenv
# source virtualenv/bin/activate
```

Install requirements:
```
# pip install --requirement=requirements.txt
```

Run tests:
```
# nosetests domain -d -v [--with-coverage  --cover-package=domain --cover-html]
```

Design
------

Scribbly ERP follows domain driven design and test driven design principles.

### Entities ###

The domain entity groups are:
- Inventory: To track movement of stock
- Warehouses: Group Inventory items at a specific physical or logical location
- Sales: Documents which describe purchase orders and invoices containing costs of goods sold
- Products: Details of goods for sale
- Taxons: Hierarchical grouping of products
- Customers: Entities which are able to purchase products and be invoiced

### Services ###

Domain services are:
- Pricing service: Calculate product discounts based on product category and customer discount tier
- Delivery service: Aggregate orders from a customer into a delivery