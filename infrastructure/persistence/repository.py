from sqlalchemy.orm.exc import NoResultFound


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