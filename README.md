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

Scribbly ERP follows domain driven design and test driver design principles.

The domain entity groups are:
- Inventory: To track movement of stock
- Sales: Documents which describe purchase orders and invoices containing costs of goods sold
- Products: Details of goods for sale
- Customers: Entities which are able to purchase products and be invoiced
