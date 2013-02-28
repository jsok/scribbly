class LineItem(object):
    """
    A line item in a sales document (Order, Invoice).
    """

    def __init__(self, sku, quantity, price, discount, tax_rate=None):
        self.sku = sku
        self.quantity = quantity
        self.price = price
        self.discount = discount
        self.tax_rate = tax_rate if tax_rate else None

    def __repr__(self):
        tax_rate = self.tax_rate if self.tax_rate else 0.00
        return "<Line Item: SKU={sku}, Quantity={quantity}, Price={price}, Discount={discount}, " \
               "TaxRate={tax_rate}".format(sku=self.sku, quantity=self.quantity, price=self.price,
                                           discount=self.discount, tax_rate=tax_rate)

    def is_taxable(self):
        return self.tax_rate is not None

    def tax(self):
        if not self.is_taxable():
            return 0.00
        else:
            return self.subtotal() * self.tax_rate

    def subtotal(self):
        return max(0, (self.price * (1.0 - self.discount)) * self.quantity)

    def total(self):
        return self.subtotal() + self.tax()