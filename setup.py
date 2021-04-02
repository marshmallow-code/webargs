import re
from setuptools import setup, find_packages

FRAMEWORKS = [
    "Flask>=0.12.5",
    "Django>=2.2.0",
    "bottle>=0.12.13",
    "tornado>=4.5.2",
    "pyramid>=1.9.1",
    "falcon>=2.0.0",
    "aiohttp>=3.0.8",
]
EXTRAS_REQUIRE = {
    "frameworks": FRAMEWORKS,
    "tests": [
        "pytest",
        "webtest==2.0.35",
        "webtest-aiohttp==2.0.0",
        "pytest-aiohttp>=0.3.0",
    ]
    + FRAMEWORKS,
    "lint": [
        "mypy==0.812",
        "flake8==3.9.0",
        "flake8-bugbear==21.4.3",
        "pre-commit~=2.4",
    ],
    "docs": ["Sphinx==3.5.3", "sphinx-issues==1.2.0", "sphinx-typlog-theme==0.8.0"]
    + FRAMEWORKS,
}
EXTRAS_REQUIRE["dev"] = EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["lint"] + ["tox"]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ""
    with open(fname) as fp:
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
        "Flask, Django, Bottle, Tornado, Pyramid, Falcon, and aiohttp."
    ),
    long_description=read("README.rst"),
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/marshmallow-code/webargs",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"webargs": ["py.typed"]},
    install_requires=["marshmallow>=3.0.0"],
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
        "request",
        "arguments",
        "validation",
        "parameters",
        "rest",
        "api",
        "marshmallow",
    ),
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
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
