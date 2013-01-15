from domain.shared.entity import Entity

class Taxon(Entity):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent if parent else None

    def path_basename(self):
        return '/' + '/'.join(self._path()[:-1])

    def path(self):
        return '/' + '/'.join(self._path())

    def _path(self):
        if self.parent is None:
            path = []
        else:
            path = self.parent._path()

        path.append(self.name)
        return path