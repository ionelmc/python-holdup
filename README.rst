========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires|
        | |coveralls|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-holdup/badge/?style=flat
    :target: https://readthedocs.org/projects/python-holdup
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.com/ionelmc/python-holdup.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.com/github/ionelmc/python-holdup

.. |requires| image:: https://requires.io/github/ionelmc/python-holdup/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ionelmc/python-holdup/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/ionelmc/python-holdup/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-holdup

.. |version| image:: https://img.shields.io/pypi/v/holdup.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/holdup

.. |wheel| image:: https://img.shields.io/pypi/wheel/holdup.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/holdup

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/holdup.svg
    :alt: Supported versions
    :target: https://pypi.org/project/holdup

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/holdup.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/holdup

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/python-holdup/v1.8.1.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/python-holdup/compare/v1.8.1...master



.. end-badges

A tool to wait for services and execute command. Useful for Docker containers that depend on slow to start services
(like almost everything).

* Free software: BSD 2-Clause License

Installation
============

::

    pip install holdup

You can also install the in-development version with::

    pip install https://github.com/ionelmc/python-holdup/archive/master.zip


Documentation
=============


https://python-holdup.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
