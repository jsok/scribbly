from domain.shared.service import Service


class PricingService(Service):

    def __init__(self, discount_repository):
        self.discount_repository = discount_repository

    def get_customer_discount(self, product, customer):
        rate = self.discount_repository.find(product.price_category, customer.discount_tier)

        if not rate:
            message = "Product Category={0} Discount Tier={1}".format(product.price_category, customer.discount_tier)
            raise PricingError("Could not find discount rate for: {0}".format(message))

        return rate.value


class PricingError(Exception):
    """
    Generic error if pricing service fails.
    """
    pass