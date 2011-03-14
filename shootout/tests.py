import unittest

from pyramid import testing


def _initTestingDB():
    from shootout.models import DBSession
    from shootout.models import Base
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

def _registerRoutes(config):
    config.add_route('idea', '/ideas/{idea_id}')
    config.add_route('user', '/users/{username}')
    config.add_route('tag', '/tags/{tag_name}')
    config.add_route('idea_add', '/idea_add')
    config.add_route('idea_vote', '/idea_vote')
    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('about', '/about')
    config.add_route('main', '/')

def _registerCommonTemplates(config):
    config.testing_add_renderer('templates/login.pt')
    config.testing_add_renderer('templates/toolbar.pt')
    config.testing_add_renderer('templates/cloud.pt')
    config.testing_add_renderer('templates/latest.pt')

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()
        self.config = testing.setUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()


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
        idea = Idea(target=target, author=user, title='title',
                    text='text')
        session.add(idea)
        session.flush()
        return idea
        
    def test_main_view(self):
        from shootout.views import main_view
        self.config.testing_securitypolicy('username')
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = main_view(request)
        self.assertEqual(result['username'], 'username')
        self.assertEqual(len(result['toplists']), 4)

    def test_idea_add_nosubmit_idea(self):
        from shootout.views import idea_add
        self.config.testing_securitypolicy('username')
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = idea_add(request)
        self.assertEqual(result['target'], None)
        self.assertEqual(result['kind'], 'idea')
        
    def test_idea_add_nosubmit_comment(self):
        from shootout.views import idea_add
        self.config.testing_securitypolicy('username')
        _registerCommonTemplates(self.config)
        idea = self._addIdea()
        request = testing.DummyRequest({'target': idea.idea_id})
        result = idea_add(request)
        self.assertEqual(result['target'], idea)
        self.assertEqual(result['kind'], 'comment')

    def test_idea_add_submit_schema_fail_empty_params(self):
        from shootout.views import idea_add
        self.config.testing_securitypolicy('username')
        _registerRoutes(self.config)
        idea = self._addIdea()
        request = testing.DummyRequest(
            params={'target': idea.idea_id, 'form.submitted': True}
        )
        result = idea_add(request)
        self.assertEqual(result.status, '302 Found')

    #def test_idea_add_submit_schema_succeed(self):
    #    from shootout.views import idea_add
    #    from shootout.models import DBSession
    #    from shootout.models import Idea
    #    self.config.testing_securitypolicy('username')
    #    request = testing.DummyRequest(
    #        params={
    #        'form.submitted':True,
    #        'tags':'abc def',
    #        'text':'My idea is cool',
    #        'title':'My idea'
    #        }
    #        )
    #    context = testing.DummyModel()
    #    user = self._addUser('username')
    #    response = idea_add(context, request)
    #    self.assertEqual(response.status, '302 Found')
    #    self.assertEqual(response.location, 'http://example.com/ideas/1')
    #    session = DBSession()
    #    result = list(session.query(Idea))
    #    self.assertEqual(len(result), 1)
    #    idea = result[0]
    #    self.assertEqual(idea.idea_id, 1)
    #    self.assertEqual(idea.text, 'My idea is cool')
    #    self.assertEqual(idea.title, 'My idea')
    #    self.assertEqual(idea.author, user.user_id)
    #    self.assertEqual(len(idea.tags), 2)
    #    self.assertEqual(idea.tags[0].name, 'abc')
    #    self.assertEqual(idea.tags[1].name, 'def')

