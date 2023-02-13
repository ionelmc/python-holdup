========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |github-actions| |requires|
        | |coveralls|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-holdup/badge/?style=flat
    :target: https://python-holdup.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/ionelmc/python-holdup/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/ionelmc/python-holdup/actions

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/python-holdup/v4.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/python-holdup/compare/v4.0.0...master



.. end-badges

A tool to wait for services and execute command. Useful for Docker containers that depend on slow to start services
(like almost everything).

* Free software: BSD 2-Clause License

Installlation
=============

Currently holdup is only published to PyPI and `hub.docker.com <https://hub.docker.com/r/ionelmc/holdup>`_.

To install from PyPI::

    pip install holdup

It has no dependencies except the optional PostgreSQL check support, which you'd install with::

    pip install 'holdup[pg]'

You can also install the in-development version with::

    pip install https://github.com/ionelmc/python-holdup/archive/master.zip

Alternate installation (Docker image)
-------------------------------------

Example::

    docker run --rm ionelmc/holdup tcp://foobar:1234

Note that this will have some limitations:

* executing the ``command`` is pretty pointless because holdup will run in its own container
* you'll probably need extra network configuration to be able to access services
* you won't be able to use `docker run` inside a container without exposing a docker daemon in said container


Usage
=====

usage: holdup [-h] [-t SECONDS] [-T SECONDS] [-i SECONDS] [-n] service [service ...] [-- command [arg [arg ...]]]

Wait for services to be ready and optionally exec command.

positional arguments:
  service
    A service to wait for. Supported protocols: "tcp://host:port/", "path:///path/to/something", "unix:///path/to/domain.sock", "eval://expr", "pg://user:password@host:port/dbname" ("postgres" and "postgresql" also allowed), "http://urn", "https://urn", "https+insecure://urn" (status 200 expected for http*). Join protocols with a comma to make holdup exit at the first passing one, eg: "tcp://host:1,host:2" or "tcp://host:1,tcp://host:2" are equivalent and mean `any that pass`.
  command
    An optional command to exec.

optional arguments:
  -h, --help            show this help message and exit
  -t SECONDS, --timeout SECONDS
                        Time to wait for services to be ready. Default: 60.0
  -T SECONDS, --check-timeout SECONDS
                        Time to wait for a single check. Default: 1.0
  -i SECONDS, --interval SECONDS
                        How often to check. Default: 0.2
  -v, --verbose         Verbose mode.
  --verbose-passwords   Disable PostgreSQL/HTTP password masking.
  -n, --no-abort        Ignore failed services. This makes `holdup` return 0 exit code regardless of services actually responding.
  --insecure            Disable SSL Certificate verification for HTTPS services.
  --version             display the version of the holdup package and its location, then exit.

Example::

    holdup tcp://foobar:1234 -- django-admin ...

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
