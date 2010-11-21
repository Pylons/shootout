import unittest

from pyramid import testing

class ViewTests(unittest.TestCase):
    def setUp(self):
        DB_STRING = 'sqlite:///:memory:'
        from shootout.models import initialize_sql
        self.engine = initialize_sql(DB_STRING, echo=False)
        testing.cleanUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.cleanUp()

    def _registerCommonTemplates(self):
        testing.registerDummyRenderer('templates/login.pt')
        testing.registerDummyRenderer('templates/toolbar.pt')
        testing.registerDummyRenderer('templates/cloud.pt')
        testing.registerDummyRenderer('templates/latest.pt')

    def _addUser(self, username='username'):
        from shootout.models import User
        from shootout.models import DBSession
        session = DBSession()
        user = User(username=username, password='password', name='name',
                    email='email')
        session.add(user)
        session.flush()
        return user

    def _addIdea(self, target=None):
        from shootout.models import Idea
        from shootout.models import DBSession
        session = DBSession()
        user = self._addUser()
        idea = Idea(target=target, author=user.user_id, title='title',
                    text='text')
        session.add(idea)
        session.flush()
        return idea
        
    def test_main_view(self):
        from shootout.views import main_view
        testing.registerDummySecurityPolicy('username')
        self._registerCommonTemplates()
        renderer = testing.registerDummyRenderer('templates/main.pt')
        request = testing.DummyRequest(params={'message':'abc'})
        context = testing.DummyModel()
        main_view(context, request)
        self.assertEqual(renderer.username, 'username')
        self.assertEqual(renderer.app_url, 'http://example.com')
        self.assertEqual(renderer.message, 'abc')
        self.assertEqual(len(renderer.toplists), 4)

    def test_idea_add_nosubmit(self):
        from shootout.views import idea_add
        testing.registerDummySecurityPolicy('username')
        self._registerCommonTemplates()
        renderer = testing.registerDummyRenderer('templates/idea_add.pt')
        request = testing.DummyRequest(params={'message':'abc'})
        context = testing.DummyModel()
        idea_add(context, request)
        self.assertEqual(renderer.app_url, 'http://example.com')
        self.assertEqual(renderer.message, 'abc')
        self.assertEqual(renderer.target, None)
        self.assertEqual(renderer.kind, 'idea')
        
    def test_idea_add_nosubmit_comment(self):
        from shootout.views import idea_add
        from shootout.models import DBSession
        testing.registerDummySecurityPolicy('username')
        self._registerCommonTemplates()
        renderer = testing.registerDummyRenderer('templates/idea_add.pt')
        idea = self._addIdea()
        request = testing.DummyRequest(
            params={'message':'abc', 'target':idea.idea_id})
        context = testing.DummyModel()
        idea_add(context, request)
        self.assertEqual(renderer.app_url, 'http://example.com')
        self.assertEqual(renderer.message, 'abc')
        self.assertEqual(renderer.target, idea)
        self.assertEqual(renderer.kind, 'comment')

    def test_idea_add_nosubmit_idea(self):
        from shootout.views import idea_add
        testing.registerDummySecurityPolicy('username')
        self._registerCommonTemplates()
        renderer = testing.registerDummyRenderer('templates/idea_add.pt')
        request = testing.DummyRequest(
            params={'message':'abc', 'target':None})
        context = testing.DummyModel()
        idea_add(context, request)
        self.assertEqual(renderer.app_url, 'http://example.com')
        self.assertEqual(renderer.message, 'abc')
        self.assertEqual(renderer.target, None)
        self.assertEqual(renderer.kind, 'idea')

    def test_idea_add_submit_schema_fail_empty_params(self):
        from shootout.views import idea_add
        from shootout.models import DBSession
        testing.registerDummySecurityPolicy('username')
        idea = self._addIdea()
        request = testing.DummyRequest(
            params={'target':idea.idea_id, 'form.submitted':True}
            )
        context = testing.DummyModel()
        response = idea_add(context, request)
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location, 'http://example.com/idea_add?message=tags%3A%20Missing%20value%0Atext%3A%20Missing%20value%0Atitle%3A%20Missing%20value')

    def test_idea_add_submit_schema_succeed(self):
        from shootout.views import idea_add
        from shootout.models import DBSession
        from shootout.models import Idea
        testing.registerDummySecurityPolicy('username')
        request = testing.DummyRequest(
            params={
            'form.submitted':True,
            'tags':'abc def',
            'text':'My idea is cool',
            'title':'My idea'
            }
            )
        context = testing.DummyModel()
        user = self._addUser('username')
        response = idea_add(context, request)
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.location, 'http://example.com/ideas/1')
        session = DBSession()
        result = list(session.query(Idea))
        self.assertEqual(len(result), 1)
        idea = result[0]
        self.assertEqual(idea.idea_id, 1)
        self.assertEqual(idea.text, 'My idea is cool')
        self.assertEqual(idea.title, 'My idea')
        self.assertEqual(idea.author, user.user_id)
        self.assertEqual(len(idea.tags), 2)
        self.assertEqual(idea.tags[0].name, 'abc')
        self.assertEqual(idea.tags[1].name, 'def')

