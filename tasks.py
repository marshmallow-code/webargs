# -*- coding: utf-8 -*-
import os
import sys
import webbrowser

from invoke import task

docs_dir = 'docs'
build_dir = os.path.join(docs_dir, '_build')

@task
def test(ctx, coverage=False, browse=False):
    flake(ctx)
    import pytest
    args = []
    if coverage:
        args.extend(['--cov=webargs', '--cov-report=term', '--cov-report=html'])

    ignores = []
    if sys.version_info < (3, 4, 1):
        ignores += [
            os.path.join('tests', 'test_aiohttpparser.py')
        ]
    if sys.version_info < (3, 5, 0):
        ignores += [
            os.path.join('tests', 'test_aiohttpparser_async_functions.py')
        ]
    if ignores:
        for each in ignores:
            args.append('--ignore={0}'.format(each))
    retcode = pytest.main(args)
    if coverage and browse:
        webbrowser.open_new_tab(os.path.join('htmlcov', 'index.html'))
    sys.exit(retcode)

@task
def flake(ctx):
    """Run flake8 on codebase."""
    cmd = 'flake8 .'
    excludes = []
    if sys.version_info < (3, 4, 1):
        excludes = [
            os.path.join('tests', 'apps', 'aiohttp_app.py'),
            os.path.join('tests', 'test_aiohttparser.py'),
            os.path.join('webargs', 'async.py'),
            os.path.join('webargs', 'async_decorators34.py'),
            os.path.join('webargs', 'aiohttpparser.py'),
            os.path.join('examples', 'annotations_example.py'),
            'build',
        ]
    if sys.version_info < (3, 5, 0):
        excludes += [
            os.path.join('webargs', 'async_decorators.py'),
            os.path.join('tests', 'test_aiohttpparser_async_functions.py'),
        ]
    if excludes:
        cmd += ' --exclude={0}'.format(','.join(excludes))
    ctx.run(cmd, echo=True)

@task
def clean(ctx):
    ctx.run('rm -rf build')
    ctx.run('rm -rf dist')
    ctx.run('rm -rf webargs.egg-info')
    clean_docs(ctx)
    print('Cleaned up.')

@task
def readme(ctx, browse=False):
    ctx.run('rst2html.py README.rst > README.html')
    if browse:
        webbrowser.open_new_tab('README.html')

@task
def clean_docs(ctx):
    ctx.run('rm -rf %s' % build_dir)

@task
def browse_docs(ctx):
    path = os.path.join(build_dir, 'index.html')
    webbrowser.open_new_tab(path)

def build_docs(ctx, browse):
    ctx.run('sphinx-build %s %s' % (docs_dir, build_dir), echo=True)
    if browse:
        browse_docs(ctx)

@task
def docs(ctx, clean=False, browse=False, watch=False):
    """Build the docs."""
    if clean:
        clean_docs(ctx)
    if watch:
        watch_docs(ctx, browse=browse)
    else:
        build_docs(ctx, browse=browse)

@task
def watch_docs(ctx, browse=False):
    """Run build the docs when a file changes."""
    try:
        import sphinx_autobuild  # noqa
    except ImportError:
        print('ERROR: watch task requires the sphinx_autobuild package.')
        print('Install it with:')
        print('    pip install sphinx-autobuild')
        sys.exit(1)
    ctx.run('sphinx-autobuild {0} {1} {2} -z webargs'.format(
        '--open-browser' if browse else '', docs_dir, build_dir), echo=True, pty=True)

@task
def publish(ctx, test=False):
    """Publish to the cheeseshop."""
    clean(ctx)
    if test:
        ctx.run('python setup.py register -r test sdist bdist_wheel', echo=True)
        ctx.run('twine upload dist/* -r test', echo=True)
    else:
        ctx.run('python setup.py register sdist bdist_wheel', echo=True)
        ctx.run('twine upload dist/*', echo=True)
