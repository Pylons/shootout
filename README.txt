shootout
========

shootout is a demo app for the Pyramid web framework.  The concepts
demonstrated in the code include:

- Urldispatch mechanism (similar to routes).

- Integration with the repoze.who authentication endware.

- Integration with the deliverance filter for theming.

- SQLAlchemy based models.

Library Requirements
--------------------

shootout requires a C compiler, SQLite3, and libxml2 and libxslt bindings.

On a Debian system, these imply: build-essentials, libsqlite3-dev,
libxml2-dev, libxslt-dev.

Installing and Running
----------------------

#. virtualenv --no-site-packages env

#. cd env

#. git clone git@github.com:Pylons/shootout.git

#. cd shootout

#. ../bin/python setup.py develop

#. ../bin/paster serve development.ini

