
Changelog
=========

1.5.1 (2018-01-30)
------------------

* Revert 5fe2cc8595115330901d890ea30adb81ef1d64c0
* Add support to skip SSL Verification for an HTTPS check (``-k|--insecure``)

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
