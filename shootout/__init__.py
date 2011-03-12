from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from sqlalchemy import engine_from_config

from shootout.models import initialize_sql


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)

    session_factory = UnencryptedCookieSessionFactoryConfig('secret')

    authn_policy = AuthTktAuthenticationPolicy('s0secret')
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(
        settings=settings,
        root_factory='shootout.models.RootFactory',
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        session_factory=session_factory
    )
    config.add_static_view('static', 'shootout:static')
    config.add_route('idea', '/ideas/{idea_id}',
                     view='shootout.views.idea_view',
                     view_renderer='templates/idea.pt')
    config.add_route('user', '/users/{username}',
                     view='shootout.views.user_view',
                     view_renderer='templates/user.pt')
    config.add_route('tag', '/tags/{tag_name}',
                     view='shootout.views.tag_view',
                     view_renderer='templates/tag.pt')
    config.add_route('idea_add', '/idea_add',
                     view='shootout.views.idea_add',
                     view_permission='post',
                     view_renderer='templates/idea_add.pt')
    config.add_route('idea_vote', '/idea_vote/{idea_id}',
                     view_permission = 'post',
                     view='shootout.views.idea_vote')
    config.add_route('register', '/register',
                     view='shootout.views.user_add',
                     view_renderer='templates/user_add.pt')
    config.add_route('login', '/login',
                     view='shootout.views.login_view')
    config.add_route('logout', '/logout',
                     view='shootout.views.logout_view')
    config.add_route('about', '/about',
                     view='shootout.views.about_view',
                     view_renderer='templates/about.pt')
    config.add_route('main', '/',
                     view='shootout.views.main_view',
                     view_renderer='templates/main.pt')
    return config.make_wsgi_app()


