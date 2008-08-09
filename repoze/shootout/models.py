from zope.interface import implements
from zope.interface import Interface

from repoze.bfg.security import Allow
from repoze.bfg.security import Everyone
from repoze.bfg.security import Authenticated

from repoze.bfg.urldispatch import RoutesMapper

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import mapper
from sqlalchemy.orm import column_property
from sqlalchemy.orm import relation

from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import MetaData
from sqlalchemy import create_engine

from repoze.who.plugins.sql import SQLAuthenticatorPlugin
from repoze.who.plugins.sql import default_password_compare

from repoze.shootout.config import DB_STRING

DBSession = scoped_session(sessionmaker(autoflush=True, autocommit=False))

def connection_factory():
    return DBSession.connection().connection.connection

def make_authenticator_plugin():
    query = "SELECT username,password FROM users where username = :login;"
    conn_factory = connection_factory
    compare_fn = default_password_compare
    return SQLAuthenticatorPlugin(query, conn_factory, compare_fn)

metadata = MetaData()

users_table = Table(
    'users',
    metadata,
    Column('user_id', Integer, primary_key=True),
    Column('username', String(20), unique=True),
    Column('password', String(20)),
    Column('name', String(50)),
    Column('email', String(50)),
    Column('hits', Integer),
    Column('misses', Integer),
    Column('delivered_hits', Integer),
    Column('delivered_misses', Integer),
)

class IUser(Interface):
    pass

class User(object):
    implements(IUser)
    def __init__(self,username,password,name,email):
        self.username=username
        self.password=password
        self.name=name
        self.email=email
        self.hits=0
        self.misses=0
        self.delivered_hits=0
        self.delivered_misses=0

user_mapper = mapper(User, users_table)

ideas_table = Table(
    'ideas',
    metadata,
    Column('idea_id', Integer, primary_key=True),
    Column('target', Integer),
    Column('author', Integer, ForeignKey('users.user_id')),
    Column('title', Text),
    Column('text', Text),
    Column('hits', Integer),
    Column('misses', Integer),
)

class IIdea(Interface):
    pass

class Idea(object):
    implements(IIdea)
    __acl__ = [ (Allow, Everyone, 'view'), ]
    def __init__(self, target, author, title, text):
       self.target = target
       self.author = author
       self.title = title
       self.text = text
       self.hits = 0
       self.misses = 0

idea_mapper = mapper(Idea, ideas_table, properties={
    'total_votes':column_property((ideas_table.c.hits+ideas_table.c.misses).label('total_votes')),
    'vote_differential':column_property((ideas_table.c.hits-ideas_table.c.misses).label('vote_differential')),
    'hit_percentage':column_property(
        ((ideas_table.c.hits>0 or ideas_table.c.misses>0) and (ideas_table.c.hits/(ideas_table.c.hits+ideas_table.c.misses)*100) or 0).label('hit_percentage')
    ),
    'users':relation(User, order_by=users_table.c.user_id),
})

class IRange(Interface):
    pass

class Range(object):
    implements(IRange)
    __acl__ = [ (Allow, Everyone, 'view'), (Allow, Authenticated, 'post')]

firing_range = Range()

def fallback_get_root(environ):
    return firing_range

def get_root():
    engine=create_engine(DB_STRING)
    DBSession.configure(bind=engine)
    metadata.bind = engine
    metadata.create_all(engine)
    root = RoutesMapper(fallback_get_root)
    root.connect('ideas/:idea', controller='ideas')
    root.connect('users/:user', controller='users')
    return root
