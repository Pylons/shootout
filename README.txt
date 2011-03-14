shootout
========

shootout is a demo app for the Pyramid web framework.  The concepts
demonstrated in the code include:

- Urldispatch mechanism (similar to routes).

- Built-in authentication and authorization mechanism.

- Integration with pyramid_simpleform for form handling.

- SQLAlchemy based models.

Library Requirements
--------------------

shootout requires a SQLite3 bindings.

On a Debian system, these imply: build-essentials, libsqlite3-dev.

Installing and Running
----------------------

#. virtualenv --no-site-packages env

#. cd env

#. . bin/activate

#. git clone git@github.com:Pylons/shootout.git

#. cd shootout

#. python setup.py develop

#. paster serve development.ini

