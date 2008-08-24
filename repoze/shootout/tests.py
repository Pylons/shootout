import unittest
from zope.testing.cleanup import cleanUp

class ViewTests(unittest.TestCase):
    def setUp(self):
        DB_STRING = 'sqlite:///:memory'
        from sqlalchemy import create_engine
        engine=create_engine(DB_STRING)
        from repoze.shootout.models import DBSession
        from repoze.shootout.models import metadata
        DBSession.configure(bind=engine)
        metadata.bind = engine
        metadata.create_all(engine)
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _registerUtility(self, impl, iface, name=''):
        import zope.component
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerUtility(impl, iface, name=name)

    def _registerTemplate(self, path, template=None):
        from repoze.bfg.interfaces import ITemplate
        from repoze.bfg.path import caller_path
        path = caller_path(path)
        if template is None:
            template = DummyTemplate()
        self._registerUtility(template, ITemplate, path)

    def test_main_view(self):
        from repoze.shootout.views import main_view
        from repoze.bfg.interfaces import ISecurityPolicy
        template = DummyTemplate()
        self._registerUtility(DummySecurityPolicy(), ISecurityPolicy)
        self._registerTemplate('templates/main.pt', template)
        self._registerTemplate('templates/login.pt')
        self._registerTemplate('templates/toolbar.pt')
        self._registerTemplate('templates/cloud.pt')
        self._registerTemplate('templates/latest.pt')
        request = DummyRequest(params={'message':'abc'})
        context = DummyContext()
        main_view(context, request)
        self.assertEqual(template.username, 'userid')
        self.assertEqual(template.app_url, 'http://app')
        self.assertEqual(template.message, 'abc')
        self.assertEqual(len(template.toplists), 4)

class DummySecurityPolicy:
    userid = 'userid'
    def authenticated_userid(self, environ):
        return self.userid

class DummyContext:
    pass

class DummyRequest:
    application_url = 'http://app'
    def __init__(self, environ=None, params=None):
        if environ is None:
            environ = {}
        self.environ = environ
        if params is None:
            params = {}
        self.params = params

class DummyTemplate:
    def template(self, **kw):
        self.__dict__.update(kw)

