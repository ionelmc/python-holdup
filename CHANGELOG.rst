
Changelog
=========

1.8.1 (2020-12-16)
------------------

* Add support for PostgreSQL 12+ clients (strict integer type-checking on ``connect_timeout``). The float is now converted to an integer.

1.8.0 (2019-05-28)
------------------

* Added a PostgreSQL check. It handles the ``the database system is starting up`` problem.
  Contributed by Dan Ailenei in `#6 <https://github.com/ionelmc/python-holdup/pull/6>`_.
* Changed output so it's more clear and more brief:

  * arguments (checks) are quoted when printed,
  * "any" checks give exact info about what made it pass,
  * repetitive information is removed.
* Simplified the internals for the "AnyCheck".

1.7.0 (2018-11-24)
------------------

* Added support for skipping SSL certificate verification for HTTPS services
  (the ``--insecure`` option and ``https+insecure`` protocol).
  Contributed by Mithun Ayachit in `#2 <https://github.com/ionelmc/python-holdup/pull/2>`_.

1.6.0 (2018-03-22)
------------------

* Added verbose mode (`-v` or ``--verbose``).
* Changed default timeout to 60s (from 5s).

1.5.0 (2017-06-07)
------------------

* Added an ``eval://expression`` protocol for weird user-defined checks.

1.4.0 (2017-03-27)
------------------

* Added support for HTTP(S) check.

1.3.0 (2017-02-21)
------------------

* Add support for "any" service check (service syntax with comma).

1.2.1 (2016-06-17)
------------------

* Handle situation where internal operations would take more than planned.

1.2.0 (2016-05-25)
------------------

* Added a file check.

1.1.0 (2016-05-06)
------------------

* Removed debug print.
* Added ``--interval`` option for how often to check. No more spinloops.

1.0.0 (2016-04-22)
------------------

* Improved tests.
* Always log to stderr.

0.1.0 (2016-04-21)
------------------

* First release on PyPI.
