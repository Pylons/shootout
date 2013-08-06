import unittest

class ViewTests(unittest.TestCase):
    def setUp(self):
        import os
        import pkg_resources
        from pyramid.paster import bootstrap
        pkgroot = pkg_resources.get_distribution('shootout').location
        testing_ini = os.path.join(pkgroot, 'testing.ini')
        env = bootstrap(testing_ini)
        self.closer = env['closer']
        from webtest import TestApp
        self.testapp = TestApp(env['app'])

    def tearDown(self):
        import transaction
        transaction.abort()
        self.closer()

    def login(self):
        self.testapp.post(
            '/register',
            {'form.submitted':'1',
             'username':'chris',
             'password':'chris',
             'confirm_password':'chris',
             'email':'chrism@plope.com',
             'name':'Chris McDonough',
             },
            status=302,
            )
        self.testapp.post(
            '/login',
            {'login':'chris', 'password':'chris'},
            status=302,
            )

    def add_idea(self):
        self.testapp.post(
            '/idea_add',
            {'form.submitted':True,
             'title':'title',
             'text':'text',
             'tags':'tag1'},
            status=302,
            )

    def test_add_idea(self):
        self.login()
        self.add_idea()
        from shootout.models import Idea
        q = Idea.get_by_tagname('tag1')
        results = q.all()
        self.assertEqual(len(results), 1)
        idea = results[0]
        self.assertEqual(idea.title, 'title')
        
    def test_idea_vote(self):
        self.login()
        self.add_idea()
        from shootout.models import Idea
        q = Idea.get_by_tagname('tag1')
        target = q.one().idea_id
        self.testapp.post(
            '/idea_vote',
            {'target':target},
            status=301,
            )

