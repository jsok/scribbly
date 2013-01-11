class HistoricalValue(object):
    '''
    An (immutable) Value at a given datetime.
    '''

    def __init__(self, value, date):
        self.value = value
        self.date = date

    def __cmp__(self, other):
        return cmp(self.date, other.date)

class HistoricalValueCollection(object):
    '''
    A set of values, each associated with a specific datetime.
    Allow querying for values at a given datetime.
    '''

    def __init__(self):
        self.history = []

    def __getitem__(self, item):
        return self.at_date(item)

    def append(self, value):
        self.history.append(value)
        self.history.sort(reverse=True)

    def at_date(self, date):
        # Get the first value in the history whose date is lte to the provided one
        return next((value for value in self.history if value.date <= date), None)

    def in_range(self, start, end):
        return next((value for value in self.history if start <= value.date <= end), None)
