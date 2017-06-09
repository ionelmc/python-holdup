========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/python-holdup/badge/?style=flat
    :target: https://readthedocs.org/projects/python-holdup
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/ionelmc/python-holdup.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ionelmc/python-holdup

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/ionelmc/python-holdup?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/ionelmc/python-holdup

.. |requires| image:: https://requires.io/github/ionelmc/python-holdup/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ionelmc/python-holdup/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/ionelmc/python-holdup/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ionelmc/python-holdup

.. |version| image:: https://img.shields.io/pypi/v/holdup.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/holdup

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/python-holdup/v1.5.0.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/python-holdup/compare/v1.5.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/holdup.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/holdup

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/holdup.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/holdup

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/holdup.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/holdup


.. end-badges

A tool to wait for services and execute command. Useful for Docker containers that depend on slow to start services
(like almost everything).

* Free software: BSD license

Installation
============

::

    pip install holdup

Documentation
=============

Usage: ``holdup [-h] [-t SECONDS] [-T SECONDS] [-i SECONDS] [-n] service [service ...] [-- command [arg [arg ...]]]``

Wait for services to be ready and optionally exec command.

Positional arguments:
  ``service``
    A service to wait for. Supported protocols:
    "tcp://host:port/", "path:///path/to/something",
    "unix:///path/to/domain.sock", "eval://expr",
    "http://urn", "http://urn" (status 200 expected). Join
    protocols with a comma to make holdup exit at the
    first passing one, eg: tcp://host:1,host:2 or
    tcp://host:1,tcp://host:2 are equivalent and mean "any
    that pass".

  ``command``
    An optional command to exec.

Optional arguments:
  -h, --help            show this help message and exit
  -t SECONDS, --timeout SECONDS
                        Time to wait for services to be ready. Default: 5.0
  -T SECONDS, --check-timeout SECONDS
                        Time to wait for a single check. Default: 1.0
  -i SECONDS, --interval SECONDS
                        How often to check. Default: 0.2
  -n, --no-abort        Ignore failed services. This makes `holdup` return 0
                        exit code regardless of services actually responding.


Development
===========

To run the all tests run::

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
