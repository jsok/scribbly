from domain.shared.entity import Entity


class Discount(Entity):
    """
    Matches a product price tier and customer discount tier to a discount value.
    """

    def __init__(self, value, product_price_category, customer_discount_tier):
        if not 0.00 <= value <= 1.00:
            raise ValueError("Discount value must between 0% and 100%")
        self.value = value

        self.product_price_category = product_price_category
        self.customer_discount_tier = customer_discount_tier