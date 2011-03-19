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
    return DBSession

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

    def _addUser(self, username=u'username'):
        from shootout.models import User
        user = User(username=username, password=u'password', name=u'name',
                    email=u'email')
        self.session.add(user)
        self.session.flush()
        return user

    def _addIdea(self, target=None, user=None):
        from shootout.models import Idea
        if not user:
            user = self._addUser()
        idea = Idea(target=target, author=user, title=u'title',
                    text=u'text')
        self.session.add(idea)
        self.session.flush()
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
        request = testing.DummyRequest(params={'target': idea.idea_id})
        result = idea_add(request)
        self.assertEqual(result['target'], idea)
        self.assertEqual(result['kind'], 'comment')

    def test_idea_add_not_existing_target(self):
        from shootout.views import idea_add
        from pyramid.httpexceptions import HTTPNotFound
        self.config.testing_securitypolicy('username')
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest(params={'target': 100})
        result = idea_add(request)
        self.assertEqual(result.code, 404)


    def test_idea_add_submit_schema_fail_empty_params(self):
        from shootout.views import idea_add
        self.config.testing_securitypolicy('username')
        _registerCommonTemplates(self.config)
        _registerRoutes(self.config)
        request = testing.DummyRequest(post={'form.submitted': 'Shoot'})
        result = idea_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'text': u'Missing value',
                'tags': u'Missing value',
                'title': u'Missing value'
            }
        )

    def test_idea_add_submit_schema_succeed(self):
        from shootout.views import idea_add
        from shootout.models import Idea
        self.config.testing_securitypolicy('username')
        _registerRoutes(self.config)
        request = testing.DummyRequest(
            post={
                'form.submitted': u'Shoot',
                'tags': u'abc def, bar',
                'text': u'My idea is cool',
                'title': u'My idea',
            }
        )
        user = self._addUser(u'username')
        result = idea_add(request)
        self.assertEqual(result.location, 'http://example.com/ideas/1')
        ideas = self.session.query(Idea).all()
        self.assertEqual(len(ideas), 1)
        idea = ideas[0]
        self.assertEqual(idea.idea_id, 1)
        self.assertEqual(idea.text, u'My idea is cool')
        self.assertEqual(idea.title, u'My idea')
        self.assertEqual(idea.author, user)
        self.assertEqual(len(idea.tags), 3)
        self.assertEqual(idea.tags[0].name, u'abc')
        self.assertEqual(idea.tags[1].name, u'bar')
        self.assertEqual(idea.tags[2].name, u'def')

    def test_positive_idea_voting(self):
        from shootout.views import idea_vote
        from shootout.models import User
        _registerRoutes(self.config)        
        idea = self._addIdea()
        user = self.session.query(User).one()
        self.assertEqual(idea.user_voted('username'), False)
        self.config.testing_securitypolicy('username')
        post_data = {
            'form.vote_hit': u'Hit',
            'target': 1,
        }
        request = testing.DummyRequest(post=post_data)
        result = idea_vote(request)
        self.assertEqual(idea.hits, 1)
        self.assertEqual(idea.misses, 0)
        self.assertEqual(idea.hit_percentage, 100)
        self.assertEqual(idea.total_votes, 1)
        self.assertEqual(idea.vote_differential, 1)
        self.assertEqual(idea.author.hits, 1)
        self.assertEqual(len(idea.voted_users.all()), 1)
        self.assertEqual(idea.voted_users.one(), user)
        self.assertTrue(idea.user_voted('username'))

    def test_negative_idea_voting(self):
        from shootout.views import idea_vote
        from shootout.models import User
        _registerRoutes(self.config)        
        idea = self._addIdea()
        user = self.session.query(User).one()
        self.assertEqual(idea.user_voted('username'), False)
        self.config.testing_securitypolicy('username')
        post_data = {
            'form.vote_miss': u'Miss',
            'target': 1,
        }
        request = testing.DummyRequest(post=post_data)
        result = idea_vote(request)
        self.assertEqual(idea.hits, 0)
        self.assertEqual(idea.misses, 1)
        self.assertEqual(idea.hit_percentage, 0)
        self.assertEqual(idea.total_votes, 1)
        self.assertEqual(idea.vote_differential, -1)
        self.assertEqual(idea.author.hits, 0)
        self.assertEqual(len(idea.voted_users.all()), 1)
        self.assertEqual(idea.voted_users.one(), user)
        self.assertTrue(idea.user_voted('username'))

    def test_registration_nosubmit(self):
        from shootout.views import user_add
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = user_add(request)
        self.assertTrue('form' in result)

    def test_registration_submit_empty(self):
        from shootout.views import user_add
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        result = user_add(request)
        self.assertTrue('form' in result)
        request = testing.DummyRequest(post={'form.submitted': 'Shoot'})
        result = user_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'username': u'Missing value',
                'confirm_password': u'Missing value',
                'password': u'Missing value',
                'email': u'Missing value',
                'name': u'Missing value'
            }
        )

    def test_registration_submit_schema_succeed(self):
        from shootout.views import user_add
        from shootout.models import User
        _registerRoutes(self.config)        
        request = testing.DummyRequest(
            post={
                'form.submitted': u'Register',
                'username': u'username',
                'password': u'secret',
                'confirm_password': u'secret',
                'email': u'username@example.com',
                'name': u'John Doe',
            }
        )
        result = user_add(request)
        users = self.session.query(User).all()
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user.username, 'username')
        self.assertEqual(user.name, u'John Doe')
        self.assertEqual(user.email, 'username@example.com')
        self.assertEqual(user.hits, 0)
        self.assertEqual(user.misses, 0)
        self.assertEqual(user.delivered_hits, 0)
        self.assertEqual(user.delivered_misses, 0)
        self.assertEqual(user.ideas, [])
        self.assertEqual(user.voted_ideas, [])

    def test_user_view(self):
        from shootout.views import user_view
        self.config.testing_securitypolicy('username')
        _registerRoutes(self.config)
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        request.matchdict = {'username': 'username'}
        user = self._addUser()
        result = user_view(request)
        self.assertEqual(result['user'].username, 'username')
        self.assertEqual(result['user'].user_id, 1)

    def test_idea_view(self):
        from shootout.views import idea_view
        self.config.testing_securitypolicy('username')
        _registerRoutes(self.config)
        _registerCommonTemplates(self.config)
        self._addIdea()
        request = testing.DummyRequest()
        request.matchdict = {'idea_id': 1}
        result = idea_view(request)
        self.assertEqual(result['idea'].title, u'title')
        self.assertEqual(result['idea'].idea_id, 1)
        self.assertEqual(result['viewer_username'], u'username')

    def test_tag_view(self):
        from shootout.views import tag_view
        from shootout.models import Tag, Idea
        self.config.testing_securitypolicy('username')
        _registerRoutes(self.config)
        _registerCommonTemplates(self.config)
        user = self._addUser()
        tag1 = Tag('bar')
        tag2 = Tag('foo')
        self.session.add_all([tag1, tag2])
        idea1 = self._addIdea(user=user)
        idea1.tags.append(tag1)
        idea2 = self._addIdea(user=user)
        idea2.tags.append(tag1)
        idea3 = self._addIdea(user=user)
        idea3.tags.append(tag2)
        self.session.flush()
        
        request = testing.DummyRequest()
        request.matchdict = {'tag_name': 'bar'}
        result = tag_view(request)
        ideas = result['ideas'].all()
        self.assertEqual(ideas[0].idea_id, idea1.idea_id)
        self.assertEqual(ideas[1].idea_id, idea2.idea_id)
        self.assertEqual(result['tag'], 'bar')

        request = testing.DummyRequest()
        request.matchdict = {'tag_name': 'foo'}
        result = tag_view(request)
        self.assertEqual(result['ideas'].one().idea_id, idea3.idea_id)
        self.assertEqual(result['tag'], 'foo')

    def test_about_view(self):
        from shootout.views import about_view
        _registerCommonTemplates(self.config)
        request = testing.DummyRequest()
        about_view(request)

    def test_login_view_submit_fail(self):
        from shootout.views import login_view
        _registerRoutes(self.config)
        self._addUser()
        request = testing.DummyRequest(
            post={
                'submit': u'Login',
                'login': u'username',
                'password': u'wrongpassword',
            }
        )
        result = login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Failed to login.'])


    def test_login_view_submit_success(self):
        from shootout.views import login_view
        _registerRoutes(self.config)
        self._addUser()
        request = testing.DummyRequest(
            post={
                'submit': u'Login',
                'login': u'username',
                'password': u'password',
            }
        )
        result = login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged in successfully.'])

    def test_logout_view(self):
        from shootout.views import logout_view
        _registerRoutes(self.config)
        request = testing.DummyRequest()
        result = logout_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged out successfully.'])
