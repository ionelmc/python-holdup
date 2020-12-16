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

.. |travis| image:: https://api.travis-ci.org/ionelmc/python-holdup.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ionelmc/python-holdup

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

Documentation
=============

Usage: ``holdup [-h] [-t SECONDS] [-T SECONDS] [-i SECONDS] [-n] [--insecure] service [service ...] [-- command [arg [arg ...]]]``

Wait for services to be ready and optionally exec command.

Positional arguments:
  ``service``
    A service to wait for. Supported protocols:
    "tcp://host:port/", "path:///path/to/something",
    "unix:///path/to/domain.sock", "eval://expr",
    "http://urn", "http://urn", "https+insecure//urn" (status 200 expected). Join
    protocols with a comma to make holdup exit at the
    first passing one, eg: tcp://host:1,host:2 or
    tcp://host:1,tcp://host:2 are equivalent and mean "any
    that pass".

  ``command``
    An optional command to exec.

Optional arguments:
  -h, --help            show this help message and exit
  -t SECONDS, --timeout SECONDS
                        Time to wait for services to be ready. Default: 60.0
  -T SECONDS, --check-timeout SECONDS
                        Time to wait for a single check. Default: 1.0
  -i SECONDS, --interval SECONDS
                        How often to check. Default: 0.2
  -n, --no-abort        Ignore failed services. This makes `holdup` return 0
                        exit code regardless of services actually responding.
  --insecure            Skip SSL Certificate verification for HTTPS services.

Suggested use
-------------

Assuming you always want the container to wait add this in your ``Dockerfile``::

    COPY entrypoint.sh /
    ENTRYPOINT ["/entrypoint.sh"]
    CMD ["/bin/bash"]

Then in ``entrypoint.sh`` you could have::

    #!/bin/sh
    set -eux
    urlstrip() { string=${@##*://}; echo ${string%%[\?/]*}; }
    exec holdup \
         "tcp://$DJANGO_DATABASE_HOST:$DJANGO_DATABASE_PORT" \
         "tcp://$(urlstrip $CELERY_RESULT_BACKEND)" \
         -- "$@"

The only disadvantage is that you might occasionally need to use ``docker run --entrypoint=''`` to avoid running holdup. No biggie.

Insecure HTTPS Service Checks
-------------------------------

You may choose to skip SSL validation when waiting for an HTTPS service (for e.g., when using an IP Address). This can be done using either of the following methods::

    # Specifying a https+insecure protocol
    holdup https+insecure://10.1.2.3/

    # Specifying the --insecure` option
    holdup --insecure https://10.1.2.3/

Skipping SSL Certificate verification requires a minimum of Python-2.7.9 or Python-3.4.3.

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
