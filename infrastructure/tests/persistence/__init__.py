from unittest import TestCase, skipUnless
from sqlalchemy import create_engine

from infrastructure.persistence import metadata


# Testing database engine:
def engine_for_testing(in_memory=None, echo=None):

    in_memory = True if in_memory else False
    echo = True if echo else False

    if in_memory:
        engine = create_engine('sqlite:///:memory:', echo=echo)
    else:
        engine = create_engine('sqlite:///infrastructure/db/testing.db', echo=echo)

    return engine


class PersistenceTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy.orm import sessionmaker
        cls.Session = sessionmaker()

    def setUp(self):
        engine = engine_for_testing(in_memory=False, echo=True)

        # connect to the database
        self.connection = engine.connect()

        # begin a non-ORM transaction
        self.trans = self.connection.begin()

        # bind an individual Session to the connection
        self.session = self.Session(bind=self.connection)

        metadata.bind = engine
        metadata.create_all(checkfirst=True)

    def tearDown(self):
    # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()
        self.session.close()

        # return connection to the Engine
        self.connection.close()
