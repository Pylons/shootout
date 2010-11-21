def make_app(global_config, **kw):
    # paster app config callback
    from repoze.shootout.models import get_root
    from repoze.shootout.models import initialize_sql
    db = kw.get('db')
    if not db:
        raise ValueError('shootout.ini requires a db section '
                         '(the SQLAlchemy db URI)')
    initialize_sql(db)
    from pyramid.configuration import Configurator
    config = Configurator(root_factory=get_root)
    config.begin()
    config.load_zcml('repoze.shootout:configure.zcml')
    config.end()
    return config.make_wsgi_app()

