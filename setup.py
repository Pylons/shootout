import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools',
    'repoze.bfg',
    'repoze.who',
    'Deliverance',
    'SQLAlchemy',
    'zope.sqlalchemy',
    'repoze.tm2',
    ]
import sys

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='repoze.shootout',
      version='0.5',
      description='A generic idea discussion and rating app',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Carlos de la Guardia',
      author_email='cguardia@yahoo.com',
      url='http://www.repoze.org',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      keywords='web wsgi bfg zope',
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['repoze'],
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="repoze.shootout.tests",
      entry_points = """\
      [paste.app_factory]
      make_app = repoze.shootout.run:make_app
      """
      )

