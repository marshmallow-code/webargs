# -*- coding: utf-8 -*-
import sys
import re
from setuptools import setup, find_packages

INSTALL_REQUIRES = ["marshmallow>=2.15.2"]
if sys.version_info[0] < 3:
    INSTALL_REQUIRES.append("simplejson>=2.1.0")

FRAMEWORKS = [
    "Flask>=0.12.2",
    "Django>=1.11.16",
    "bottle>=0.12.13",
    "tornado>=4.5.2",
    "pyramid>=1.9.1",
    "webapp2>=3.0.0b1",
    "falcon>=1.4.0,<2.0",
    'aiohttp>=3.0.0; python_version >= "3.5"',
]
EXTRAS_REQUIRE = {
    "frameworks": FRAMEWORKS,
    "tests": [
        "pytest",
        "mock",
        "webtest==2.0.33",
        'webtest-aiohttp==2.0.0; python_version >= "3.5"',
        'pytest-aiohttp>=0.3.0; python_version >= "3.5"',
    ]
    + FRAMEWORKS,
    "lint": [
        'mypy==0.730; python_version >= "3.5"',
        "flake8==3.7.8",
        'flake8-bugbear==19.8.0; python_version >= "3.5"',
        "pre-commit~=1.17",
    ],
    "docs": ["Sphinx==2.2.0", "sphinx-issues==1.2.0", "sphinx-typlog-theme==0.7.3"]
    + FRAMEWORKS,
}
EXTRAS_REQUIRE["dev"] = EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["lint"] + ["tox"]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ""
    with open(fname, "r") as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError("Cannot find version information")
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name="webargs",
    version=find_version("src/webargs/__init__.py"),
    description=(
        "Declarative parsing and validation of HTTP request objects, "
        "with built-in support for popular web frameworks, including "
        "Flask, Django, Bottle, Tornado, Pyramid, webapp2, Falcon, and aiohttp."
    ),
    long_description=read("README.rst"),
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/marshmallow-code/webargs",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    license="MIT",
    zip_safe=False,
    keywords=(
        "webargs",
        "http",
        "flask",
        "django",
        "bottle",
        "tornado",
        "aiohttp",
        "webapp2",
        "request",
        "arguments",
        "validation",
        "parameters",
        "rest",
        "api",
        "marshmallow",
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    test_suite="tests",
    project_urls={
        "Changelog": "https://webargs.readthedocs.io/en/latest/changelog.html",
        "Issues": "https://github.com/marshmallow-code/webargs/issues",
        "Funding": "https://opencollective.com/marshmallow",
        "Tidelift": "https://tidelift.com/subscription/pkg/pypi-webargs?utm_source=pypi-marshmallow&utm_medium=pypi",  # noqa
    },
)
