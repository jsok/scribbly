class Repository(object):
    """
    Abstract base class for Repository pattern.
    """

    def create(self, obj):
        raise NotImplementedError()

    def find(self, id):
        raise NotImplementedError()

    def store(self, obj):
        raise NotImplementedError()

    def delete(self, id):
        raise NotImplementedError()