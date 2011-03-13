from pyramid.renderers import get_renderer


def add_base_template(event):
    base = get_renderer('templates/base.pt').implementation()
    event.update({'base': base})
