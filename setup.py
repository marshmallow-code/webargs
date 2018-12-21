# -*- coding: utf-8 -*-
import re
from setuptools import setup, find_packages

INSTALL_REQUIRES = ["marshmallow>=2.15.2"]
FRAMEWORKS = [
    "Flask>=0.12.2",
    "Django>=1.11.16",
    "bottle>=0.12.13",
    "tornado>=4.5.2",
    "pyramid>=1.8.5",
    "webapp2>=3.0.0b1",
    "falcon>=1.3.0",
    'aiohttp>=3.0.0; python_version >= "3.5"',
]
EXTRAS_REQUIRE = {
    "frameworks": FRAMEWORKS,
    "tests": [
        "pytest",
        "mock",
        "webtest==2.0.32",
        'webtest-aiohttp==2.0.0; python_version >= "3.5"',
        'pytest-aiohttp>=0.3.0; python_version >= "3.5"',
    ]
    + FRAMEWORKS,
    "lint": [
        "flake8==3.6.0",
        'flake8-bugbear==18.8.0; python_version >= "3.5"',
        "pre-commit==1.13.0",
    ],
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


__version__ = find_version("webargs/__init__.py")


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name="webargs",
    version=__version__,
    description=(
        "A friendly library for parsing and validating HTTP request arguments, "
        "with built-in support for popular web frameworks, including "
        "Flask, Django, Bottle, Tornado, Pyramid, webapp2, Falcon, and aiohttp."
    ),
    long_description=read("README.rst"),
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/sloria/webargs",
    packages=find_packages(exclude=("test*", "examples")),
    package_dir={"webargs": "webargs"},
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
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    test_suite="tests",
    project_urls={
        "Issues": "https://github.com/sloria/webargs/issues",
        "Changelog": "https://webargs.readthedocs.io/en/latest/changelog.html",
    },
)
