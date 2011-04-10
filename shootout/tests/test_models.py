# -*- coding: utf-8 -*-
import unittest

from pyramid import testing


def _initTestingDB():
    from shootout.models import DBSession
    from shootout.models import Base
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    session = DBSession()
    session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return session


class ModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()

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


class TestUser(ModelsTestCase):
    def test_add_user(self):
        from shootout.models import User
        user = User(u'username', u'password', u'name', u'email')
        self.session.add(user)
        self.session.flush()
        user = self.session.query(User).filter(User.username == u'username')
        user = user.first()
        self.assertEqual(user.username, u'username')
        self.assertEqual(user.name, u'name')
        self.assertEqual(user.email, u'email')
        self.assertEqual(user.hits, 0)
        self.assertEqual(user.misses, 0)
        self.assertEqual(user.delivered_hits, 0)
        self.assertEqual(user.delivered_misses, 0)

    def test_password_hashing(self):
        import cryptacular.bcrypt
        crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
        user = self._addUser()
        self.assertTrue(crypt.check(user.password, u'password'))

    def test_password_checking(self):
        from shootout.models import User
        user = self._addUser()
        self.assertTrue(User.check_password(u'username', u'password'))
        self.assertFalse(User.check_password(u'username', u'wrong'))
        self.assertFalse(User.check_password(u'nobody', u'password'))

    def test_getting_by_username(self):
        from shootout.models import User
        user = self._addUser()
        self.assertEqual(user, User.get_by_username(u'username'))
       

class TestTag(ModelsTestCase):
    def test_extracting_tags(self):
        from shootout.models import Tag
        tags_string = u'foo, bar; baz xxx,, yyy, zzz'
        expected_tags = set([
            u'foo', u'bar', u'baz', u'xxx', u'yyy', u'zzz'
        ])
        extracted_tags = Tag.extract_tags(tags_string)
        self.assertEqual(extracted_tags, expected_tags)

    def test_creating_tags(self):
        from shootout.models import Tag
        tags = Tag.create_tags(u'foo bar baz')
        tags_names = set([u'foo', u'bar', u'baz'])
        self.assertEqual(tags[0].name, tags_names.pop())
        self.assertEqual(tags[1].name, tags_names.pop())
        self.assertEqual(tags[2].name, tags_names.pop())

    def test_tags_counts(self):
        from shootout.models import Tag, Idea

        user = self._addUser()

        idea1 = self._addIdea(user=user)
        idea1.tags = Tag.create_tags(u'foo bar baz')
        self.session.add(idea1)
        idea2 = self._addIdea(user=user)
        idea2.tags = Tag.create_tags(u'baz zzz aaa')
        self.session.add(idea2)
        idea2 = self._addIdea(user=user)
        idea2.tags = Tag.create_tags(u'foo baz')
        self.session.add(idea2)
        self.session.flush()

        tags_counts = Tag.tag_counts()
        expected_counts = [
            ('aaa', 1),
            ('bar', 1),
            ('baz', 3),
            ('foo', 2),
            ('zzz', 1),
        ]
        self.assertEqual(list(tags_counts), expected_counts)

