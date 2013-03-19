from infrastructure.persistence.sqlalchemy import Session


class SqlAlchemyRepository(object):

    def __init__(self):
        self.session = Session()