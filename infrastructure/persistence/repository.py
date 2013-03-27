from sqlalchemy.orm.exc import NoResultFound

#from infrastructure.persistence import Session


class Repository(object):
    def __init__(self, session):
        self.session = session

    def find(self, query):
        try:
            return query.one()
        except NoResultFound:
            return None
        except:
            raise
