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

Domain
------

Scribbly ERP follows domain driven design and test driven design principles.

### Entities ###

The domain entity groups are:
- Inventory: To track movement of stock
- Sales: Documents which describe purchase orders and invoices containing costs of goods sold
- Products: Details of goods for sale
- Taxons: Hierarchical grouping of products
- Customers: Entities which are able to purchase products and be invoiced

### Services ###

Domain services are:
- Pricing service: Calculate product discounts based on product category and customer discount tier
- Ordering service: Collect orders and acknowledge them
- Delivery service: Aggregate orders from a customer into a delivery
- Invoicing service: Create invoices for deliveries, orders or ad-hoc

### Tests ###

Run tests:
```
# nosetests domain -d -v [--with-coverage --cover-branches --cover-package=domain --cover-html]
```

Infrastructure
--------------

### Persistence ###

Comprised of:
- SQLAlchemy: Database library used to perform all database calls
- alembic: Migrations tool

### Tests ###

Run tests:
```
# nosetests infrastructure -d -v -s
```

Options available:

- `export SQLITE_ECHO=1` for more database engine verbosity
- `export SQLITE_IN_MEMORY=1` to run tests on in-memory sqlite instance