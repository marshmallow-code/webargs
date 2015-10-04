# -*- coding: utf-8 -*-
import re
from setuptools import setup, find_packages

# Requirements
REQUIREMENTS = ['marshmallow>=2.0.0']

def find_version(fname):
    '''Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    '''
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version

__version__ = find_version("webargs/__init__.py")


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content

setup(
    name='webargs',
    version=__version__,
    description=('A friendly library for parsing HTTP request arguments, '
        'with built-in support for popular web frameworks, including '
        'Flask, Django, Bottle, Tornado, Pyramid, webapp2, and Falcon.'),
    long_description=read("README.rst"),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/sloria/webargs',
    packages=find_packages(exclude=("test*", 'examples')),
    package_dir={'webargs': 'webargs'},
    install_requires=REQUIREMENTS,
    license=read("LICENSE"),
    zip_safe=False,
    keywords=('webargs', 'http', 'flask', 'django', 'bottle', 'tornado',
      'webapp2', 'request', 'arguments', 'parameters', 'rest', 'api', 'marshmallow'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    test_suite='tests',
)
