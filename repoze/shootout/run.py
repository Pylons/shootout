def make_app(global_config, **kw):
    # paster app config callback
    from repoze.bfg.router import make_app
    from repoze.shootout.models import get_root
    from repoze.shootout.models import initialize_sql
    db = kw.get('db')
    if not db:
        raise ValueError('shootout.ini requires a db section '
                         '(the SQLAlchemy db URI)')
    initialize_sql(db)
    import repoze.shootout
    app = make_app(get_root, repoze.shootout)
    return app

