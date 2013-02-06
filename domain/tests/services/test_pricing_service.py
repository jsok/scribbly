from mock import Mock
from unittest import TestCase

from domain.model.pricing.discount import Discount
from domain.service.pricing_service import PricingService

from domain.tests.factories.customer import CustomerFactory
from domain.tests.factories.product import ProductFactory

class PricingServiceTestCase(TestCase):

    def setUp(self):
        self.repo = Mock()

        self.repo.find = Mock()
        self.repo.find.return_value = Discount(0.3, "MANF-A", "GRADE-A")

        self.service = PricingService(self.repo)

    def test_customer_discount(self):
        product = ProductFactory.build(price_category="MANF-A")
        customer = CustomerFactory.build(discount_tier="GRADE-A")

        discount = self.service.get_customer_discount(product, customer)

        self.assertEquals(0.3, discount, "Wrong discount calculated")
        self.repo.find.assert_called_with("MANF-A", "GRADE-A")