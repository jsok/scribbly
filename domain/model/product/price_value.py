import datetime

from domain.shared.historical_value import HistoricalValue

class PriceValue(HistoricalValue):
    '''
    A price of a product at a particular point in time.
    '''

    def __init__(self, price, date):
        super(PriceValue, self).__init__(price, date)