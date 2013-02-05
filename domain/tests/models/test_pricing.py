from unittest import TestCase
from nose.tools import raises

from domain.model.pricing.discount import Discount
from domain.model.pricing.tax_rate import TaxRate

class DiscountTestCase(TestCase):

    @raises(ValueError)
    def test_discount_invalid_value(self):
        discount = Discount(1.1, "MANF-A", "GRADE-A")

    def test_discount_valid(self):
        discount = Discount(0.3, "MANF-A", "GRADE-A")

        self.assertEquals(0.3, discount.value, "Wrong discount value set")

class TaxRateTestCase(TestCase):

    @raises(ValueError)
    def test_tax_rate_invalid(self):
        rate = TaxRate("GST", 10)

    def test_tax_rate(self):
        rate = TaxRate("GST", 0.10)

        self.assertEquals(0.10, rate.rate, "Wrong tax rate was set")