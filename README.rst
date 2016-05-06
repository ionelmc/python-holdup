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
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

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

.. |version| image:: https://img.shields.io/pypi/v/holdup.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/holdup

.. |downloads| image:: https://img.shields.io/pypi/dm/holdup.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/holdup

.. |wheel| image:: https://img.shields.io/pypi/wheel/holdup.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/holdup

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/holdup.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/holdup

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/holdup.svg?style=flat
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

Usage: ``holdup [-h] [-t SECONDS] [-i SECONDS] [-n] service [service ...] [-- command [arg [arg ...]]]``

Wait for services to be ready and optionally exec command.

positional arguments:
  service               A service to wait for. Supported protocols: "tcp://host:port/", "unix:///path/to/domain.sock".
  command               An optional command to exec.

optional arguments:
  -h, --help            Show this help message and exit.
  -t SECONDS, --timeout SECONDS
                        Time to wait for services to be ready. Default: 5.0
  -i SECONDS, --interval SECONDS
                        How often to check. Default: 0.2
  -n, --no-abort        Ignore failed services. This makes `holdup` return 0 exit code regardless of services actually responding.

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
