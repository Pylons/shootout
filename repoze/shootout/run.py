def make_app(global_config, **kw):
    # paster app config callback
    from repoze.bfg import make_app
    from repoze.shootout.models import get_root
    import repoze.shootout
    app = make_app(get_root(), repoze.shootout)
    return app

if __name__ == '__main__':
    from paste import httpserver
    app = make_app(None)
    httpserver.serve(app, host='0.0.0.0', port='5431')
    
