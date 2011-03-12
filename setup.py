import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools',
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'repoze.tm2>=1.0b1', # default_commit_veto
    'zope.sqlalchemy',
    'WebError',
    'formencode',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='shootout',
      version='0.2',
      description='A generic idea discussion and rating app (Pyramid sample)',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Framework :: Pylons",
        "Framework :: BFG",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author="Carlos de la Guardia, Lukasz Fidosz",
      author_email="cguardia@yahoo.com, virhilo@gmail.com",
      url='http://pylons-devel@googlegroups.com',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      keywords='web wsgi pyramid pylons example',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='shootout.tests',
      install_requires = requires,
      entry_points = """\
      [paste.app_factory]
      main = shootout:main
      """,
      paster_plugins=['pyramid'],
      )

