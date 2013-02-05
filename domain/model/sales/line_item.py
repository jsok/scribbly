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