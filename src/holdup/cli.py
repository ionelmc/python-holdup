"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mholdup` python will execute
    ``__main__.py`` as a script. That means there will not be any
    ``holdup.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there"s no ``holdup.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import argparse
import os
import sys
from operator import methodcaller
from shlex import quote
from time import sleep
from time import time

from . import __version__
from .checks import AnyCheck
from .checks import EvalCheck
from .checks import HttpCheck
from .checks import PathCheck
from .checks import PgCheck
from .checks import TcpCheck
from .checks import UnixCheck
from .pg import make_conninfo
from .pg import psycopg


def parse_service(service):
    if "://" not in service:
        raise argparse.ArgumentTypeError(f'Invalid service spec {service!r}. Must have "://".')
    proto, value = service.split("://", 1)

    if "," in value and proto != "eval":
        parts = value.split(",")
        for pos, part in enumerate(parts):
            if part.startswith("eval://"):
                parts[pos] = ",".join(parts[pos:])
                del parts[pos + 1 :]
                break
        return AnyCheck([parse_value(part, proto) for part in parts])
    else:
        return parse_value(value, proto)


def parse_value(value, proto):
    if "://" in value:
        proto, value = value.split("://", 1)
    display_value = f"{proto}://{value}"

    if proto == "tcp":
        if ":" not in value:
            raise argparse.ArgumentTypeError(f'Invalid service spec {display_value!r}. Must have ":". Where\'s the port?')
        host, port = value.strip("/").split(":", 1)
        if not port.isdigit():
            raise argparse.ArgumentTypeError(f"Invalid service spec {display_value!r}. Port must be a number not {port!r}.")
        port = int(port)
        return TcpCheck(host, port)
    elif proto in ("pg", "postgresql", "postgres"):
        if psycopg is None:
            raise argparse.ArgumentTypeError(f"Protocol {proto} unusable. Install holdup[pg].")

        uri = f"postgresql://{value}"
        try:
            connection_uri = make_conninfo(uri)
        except Exception as exc:
            raise argparse.ArgumentTypeError(f"Failed to parse {display_value!r}: {exc}. Must be a valid connection URI.") from None
        return PgCheck(connection_uri)
    elif proto == "unix":
        return UnixCheck(value)
    elif proto == "path":
        return PathCheck(value)
    elif proto in ("http", "https", "https+insecure"):
        return HttpCheck(f"{proto}://{value}")
    elif proto == "eval":
        return EvalCheck(value)
    else:
        raise argparse.ArgumentTypeError(f'Unknown protocol {proto!r} in {display_value!r}. Must be "tcp", "path", "unix" or "pg".')


parser = argparse.ArgumentParser(
    usage="%(prog)s [-h] [-t SECONDS] [-T SECONDS] [-i SECONDS] [-n] service [service ...] " "[-- command [arg [arg ...]]]",
    description="Wait for services to be ready and optionally exec command.",
)
parser.add_argument(
    "service",
    nargs=argparse.ONE_OR_MORE,
    type=parse_service,
    help="A service to wait for. "
    "Supported protocols: "
    '"tcp://host:port/", '
    '"path:///path/to/something", '
    '"unix:///path/to/domain.sock", '
    '"eval://expr", '
    '"pg://user:password@host:port/dbname" ("postgres" and "postgresql" also allowed), '
    '"http://urn", '
    '"https://urn", '
    '"https+insecure://urn" (status 200 expected for http*). '
    "Join protocols with a comma to make holdup exit at the first "
    'passing one, eg: "tcp://host:1,host:2" or "tcp://host:1,tcp://host:2" are equivalent and mean '
    "`any that pass`.",
)
parser.add_argument("command", nargs=argparse.OPTIONAL, help="An optional command to exec.")
parser.add_argument(
    "-t", "--timeout", metavar="SECONDS", type=float, default=60.0, help="Time to wait for services to be ready. Default: %(default)s"
)
parser.add_argument(
    "-T", "--check-timeout", metavar="SECONDS", type=float, default=1.0, help="Time to wait for a single check. Default: %(default)s"
)
parser.add_argument("-i", "--interval", metavar="SECONDS", type=float, default=0.2, help="How often to check. Default: %(default)s")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode.")
parser.add_argument("--verbose-passwords", action="store_true", help="Disable PostgreSQL/HTTP password masking.")
parser.add_argument(
    "-n",
    "--no-abort",
    action="store_true",
    help="Ignore failed services. " "This makes `holdup` return 0 exit code regardless of services actually responding.",
)
parser.add_argument("--insecure", action="store_true", help="Disable SSL Certificate verification for HTTPS services.")


def add_version_argument(parser):
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{__version__}",
        help="display the version of the holdup package and its location, then exit.",
    )


def main():
    """
    Args:
        argv (list): List of arguments

    Returns:
        int: A return code

    Does stuff.
    """
    add_version_argument(parser)
    if "--" in sys.argv:
        pos = sys.argv.index("--")
        argv, command = sys.argv[1:pos], sys.argv[pos + 1 :]
    else:
        argv, command = sys.argv[1:], None
    options = parser.parse_args(args=argv)
    if options.timeout < options.check_timeout:
        if options.check_timeout == 1.0:
            options.check_timeout = options.timeout
        else:
            parser.error("--timeout value must be greater than --check-timeout value!")
    pending = list(options.service)
    brief_representer = methodcaller("display", verbose=False, verbose_passwords=options.verbose_passwords)
    verbose_representer = methodcaller("display", verbose=True, verbose_passwords=options.verbose_passwords)
    if options.verbose:
        print(
            f"holdup: Waiting for {options.timeout}s ({options.check_timeout}s per check, {options.interval}s sleep between loops) "
            f'for these services: {", ".join(map(brief_representer, pending))}'
        )
    start = time()
    at_least_once = True
    while at_least_once or pending and time() - start < options.timeout:
        lapse = time()
        pending = [check for check in pending if not check.is_passing(options)]
        sleep(max(0, options.interval - time() + lapse))
        at_least_once = False

    if pending:
        if options.no_abort:
            print(
                f'holdup: Failed checks: {", ".join(map(verbose_representer, pending))}. Treating as success because of --no-abort.',
                file=sys.stderr,
            )
        else:
            parser.exit(1, f'holdup: Failed checks: {", ".join(map(verbose_representer, pending))}. Aborting!\n')
    if command:
        if options.verbose:
            print(f'holdup: Executing: {" ".join(map(quote, command))}')
        os.execvp(command[0], command)  # noqa:S606
