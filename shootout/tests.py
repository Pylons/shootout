import unittest
from pyramid.config import Configurator
from pyramid import testing

def _initTestingDB():
    from sqlalchemy import create_engine
    from shootout.models import initialize_sql
    session = initialize_sql(create_engine('sqlite://'))
    return session

class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def test_it(self):
        from shootout.views import my_view
        request = testing.DummyRequest()
        info = my_view(request)
        self.assertEqual(info['root'].name, 'root')
        self.assertEqual(info['project'], 'shootout')
