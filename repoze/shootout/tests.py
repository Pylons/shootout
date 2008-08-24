import unittest
import transaction
import zope.component

from zope.testing.cleanup import cleanUp # import alias
from repoze.bfg.path import caller_path
from repoze.bfg.interfaces import ITemplate
from repoze.bfg.interfaces import ISecurityPolicy

class ViewTests(unittest.TestCase):
    def setUp(self):
        DB_STRING = 'sqlite:///:memory:'
        from repoze.shootout.models import initialize_sql
        self.engine = initialize_sql(DB_STRING, echo=False)
        cleanUp()

    def tearDown(self):
        transaction.abort()
        cleanUp()

    def _registerCommonTemplates(self):
        registerTemplate('templates/login.pt')
        registerTemplate('templates/toolbar.pt')
        registerTemplate('templates/cloud.pt')
        registerTemplate('templates/latest.pt')

    def _addIdea(self, target=None):
        from repoze.shootout.models import Idea
        from repoze.shootout.models import User
        from repoze.shootout.models import DBSession
        session = DBSession()
        user = User(username='username', password='password', name='name',
                    email='email')
        session.save(user)
        session.flush()
        idea = Idea(target=target, author=user.user_id, title='title',
                    text='text')
        session.add(idea)
        session.flush()
        return idea
        
    def test_main_view(self):
        from repoze.shootout.views import main_view
        registerSecurityPolicy(DummySecurityPolicy('userid'))
        self._registerCommonTemplates()
        template = DummyTemplate()
        registerTemplate('templates/main.pt', template)
        request = DummyRequest(params={'message':'abc'})
        context = DummyContext()
        main_view(context, request)
        self.assertEqual(template.username, 'userid')
        self.assertEqual(template.app_url, 'http://app')
        self.assertEqual(template.message, 'abc')
        self.assertEqual(len(template.toplists), 4)

    def test_idea_add_nosubmit(self):
        from repoze.shootout.views import idea_add
        registerSecurityPolicy(DummySecurityPolicy('userid'))
        self._registerCommonTemplates()
        template = DummyTemplate()
        registerTemplate('templates/idea_add.pt', template)
        request = DummyRequest(params={'message':'abc'})
        context = DummyContext()
        idea_add(context, request)
        self.assertEqual(template.app_url, 'http://app')
        self.assertEqual(template.message, 'abc')
        self.assertEqual(template.target, None)
        self.assertEqual(template.kind, 'idea')
        
    def test_idea_add_nosubmit_comment(self):
        from repoze.shootout.views import idea_add
        from repoze.shootout.models import DBSession
        registerSecurityPolicy(DummySecurityPolicy('userid'))
        self._registerCommonTemplates()
        template = DummyTemplate()
        registerTemplate('templates/idea_add.pt', template)
        idea = self._addIdea()
        session = DBSession()
        request = DummyRequest(params={'message':'abc', 'target':idea.idea_id})
        context = DummyContext()
        idea_add(context, request)
        self.assertEqual(template.app_url, 'http://app')
        self.assertEqual(template.message, 'abc')
        self.assertEqual(template.target, idea)
        self.assertEqual(template.kind, 'comment')
        
def registerUtility(impl, iface, name=''):
    gsm = zope.component.getGlobalSiteManager()
    gsm.registerUtility(impl, iface, name=name)
    
def registerTemplate(path, template=None):
    path = caller_path(path)
    if template is None:
        template = DummyTemplate()
    registerUtility(template, ITemplate, path)

def registerSecurityPolicy(policy):
    registerUtility(policy, ISecurityPolicy)

class DummySecurityPolicy:
    def __init__(self, userid=None):
        self.userid = userid

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

