import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools>=1.0a6',
    'pyramid',
    'repoze.who',
    'repoze.who.deprecatedplugins',
    'Deliverance <= 0.2',
    'SQLAlchemy < 0.6a',
    'zope.sqlalchemy',
    'repoze.tm2',
    'FormEncode',
    ]
import sys

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='shootout',
      version='0.0',
      description='A generic idea discussion and rating app (Pyramid sample)',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Framework :: Pylons",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Carlos de la Guardia',
      author_email='cguardia@yahoo.com',
      url='http://pylons-devel@googlegroups.com',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      keywords='web wsgi pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="shootout.tests",
      entry_points = """\
      [paste.app_factory]
      main = shootout:main
      """
      )

