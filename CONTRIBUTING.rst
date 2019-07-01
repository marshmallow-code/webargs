Contributing Guidelines
=======================

Security Contact Information
----------------------------

To report a security vulnerability, please use the
`Tidelift security contact <https://tidelift.com/security>`_.
Tidelift will coordinate the fix and disclosure.

Questions, Feature Requests, Bug Reports, and Feedback…
-------------------------------------------------------

…should all be reported on the `GitHub Issue Tracker`_ .

.. _`GitHub Issue Tracker`: https://github.com/marshmallow-code/webargs/issues?state=open


Contributing Code
-----------------

In General
++++++++++

- `PEP 8`_, when sensible.
- Test ruthlessly. Write docs for new features.
- Even more important than Test-Driven Development--*Human-Driven Development*.

.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/

In Particular
+++++++++++++


Integration with a Another Web Framework…
*****************************************

…should be released as a separate package.

**Pull requests adding support for another framework will not be
accepted**. In order to keep webargs small and easy to maintain, we are
not currently adding support for more frameworks. Instead, release your
framework integration as a separate package and add it to the
`Ecosystem <https://github.com/marshmallow-code/webargs/wiki/Ecosystem>`_ page in
the `GitHub wiki <https://github.com/marshmallow-code/webargs/wiki/Ecosystem>`_ .

Setting Up for Local Development
********************************

1. Fork webargs_ on GitHub.

::

    $ git clone https://github.com/marshmallow-code/webargs.git
    $ cd webargs

2. Install development requirements. **It is highly recommended that you use a virtualenv.**
   Use the following command to install an editable version of
   webargs along with its development requirements.

::

    # After activating your virtualenv
    $ pip install -e '.[dev]'

3. (Optional, but recommended) Install the pre-commit hooks, which will format and lint your git staged files.

::

    # The pre-commit CLI was installed above
    $ pre-commit install

.. note::

    webargs uses `black <https://github.com/ambv/black>`_ for code formatting, which is only compatible with Python>=3.6. Therefore, the ``pre-commit install`` command will only work if you have the ``python3.6`` interpreter installed.

Git Branch Structure
********************

Webargs abides by the following branching model:


``dev``
    Current development branch. **New features should branch off here**.

``X.Y-line``
    Maintenance branch for release ``X.Y``. **Bug fixes should be sent to the most recent release branch.**. The maintainer will forward-port the fix to ``dev``. Note: exceptions may be made for bug fixes that introduce large code changes.

**Always make a new branch for your work**, no matter how small. Also, **do not put unrelated changes in the same branch or pull request**. This makes it more difficult to merge your changes.

Pull Requests
**************

1. Create a new local branch.

::

    # For a new feature
    $ git checkout -b name-of-feature dev

    # For a bugfix
    $ git checkout -b fix-something 1.2-line

2. Commit your changes. Write `good commit messages <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.

::

    $ git commit -m "Detailed commit message"
    $ git push origin name-of-feature

3. Before submitting a pull request, check the following:

- If the pull request adds functionality, it is tested and the docs are updated.
- You've added yourself to ``AUTHORS.rst``.

4. Submit a pull request to ``marshmallow-code:dev`` or the appropriate maintenance branch.
The `CI <https://dev.azure.com/sloria/sloria/_build/latest?definitionId=6&branchName=dev>`_ build must be passing before your pull request is merged.

Running Tests
*************

To run all tests: ::

    $ pytest

To run syntax checks: ::

    $ tox -e lint

(Optional) To run tests on Python 2.7, 3.5, 3.6, and 3.7 virtual environments (must have each interpreter installed): ::

    $ tox

Documentation
*************

Contributions to the documentation are welcome. Documentation is written in `reStructured Text`_ (rST). A quick rST reference can be found `here <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_. Builds are powered by Sphinx_.

To build the docs in "watch" mode: ::

   $ tox -e watch-docs

Changes in the `docs/` directory will automatically trigger a rebuild.

Contributing Examples
*********************

Have a usage example you'd like to share? Feel free to add it to the `examples <https://github.com/marshmallow-code/webargs/tree/dev/examples>`_ directory and send a pull request.


.. _Sphinx: http://sphinx.pocoo.org/
.. _`reStructured Text`: http://docutils.sourceforge.net/rst.html
.. _webargs: https://github.com/marshmallow-code/webargs
