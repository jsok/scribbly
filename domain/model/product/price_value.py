import datetime

class PriceValue(object):
    '''
    A price of a product at a particular point in time.
    '''

    def __init__(self, price, date):
        self.price = price
        self.date = date

    def __cmp__(self, other):
        return cmp(self.date, other.date)
