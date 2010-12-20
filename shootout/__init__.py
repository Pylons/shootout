from shootout.models import get_root
from shootout.models import initialize_sql

def main(global_config, **settings):
    # paster app config callback
    db = settings.get('db')
    if not db:
        raise ValueError('shootout requires a db section '
                         '(the SQLAlchemy db URI)')
    initialize_sql(db)
    from pyramid.config import Configurator
    config = Configurator(root_factory=get_root)
    config.load_zcml('shootout:configure.zcml')
    return config.make_wsgi_app()

