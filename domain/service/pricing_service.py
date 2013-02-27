from domain.shared.service import Service


class PricingService(Service):

    def __init__(self, discount_repository):
        self.discount_repository = discount_repository

    def get_customer_discount(self, product, customer):
        rate = self.discount_repository.find(product.price_category, customer.discount_tier)

        return rate.value
