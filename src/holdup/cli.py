"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mholdup` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``holdup.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``holdup.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import argparse
import ast
import os
import re
import socket
import ssl
import sys
from contextlib import closing
from operator import methodcaller
from time import sleep
from time import time

try:
    import psycopg
except ImportError:
    try:
        import psycopg2 as psycopg
    except ImportError:
        try:
            import psycopg2cffi as psycopg
        except ImportError:
            psycopg = None
try:
    from psycopg.conninfo import make_conninfo
except ImportError:
    try:
        from psycopg2.extensions import make_dsn as make_conninfo
    except ImportError:
        make_conninfo = lambda value: value  # noqa

import builtins
from pipes import quote
from urllib.parse import urlparse
from urllib.parse import urlunparse
from urllib.request import HTTPBasicAuthHandler
from urllib.request import HTTPDigestAuthHandler
from urllib.request import HTTPPasswordMgrWithDefaultRealm
from urllib.request import HTTPSHandler
from urllib.request import build_opener


class Check(object):
    error = None

    def is_passing(self, options):
        try:
            self.run(options)
        except Exception as exc:
            self.error = exc
        else:
            self.error = False
            if options.verbose:
                print(f"holdup: Passed check: {self.display(verbose=True, verbose_passwords=options.verbose_passwords)}")
            return True

    def run(self, options):
        raise NotImplementedError

    @property
    def status(self):
        if self.error:
            return f"{self.error}"
        elif self.error is None:
            return "PENDING"
        else:
            return "PASSED"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.__dict__)[1:-1]})"

    def display_definition(self, **kwargs):
        raise NotImplementedError

    def display(self, *, verbose, **kwargs):
        definition = self.display_definition(**kwargs)
        if verbose:
            return f"{definition!r} -> {self.status}"
        else:
            return definition


class TcpCheck(Check):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def run(self, options):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(options.check_timeout)
        with closing(sock):
            sock.connect((self.host, self.port))

    def __repr__(self):
        return f"TcpCheck(host={self.host!r}, port={self.port!r})"

    def display(self, *, verbose, **_):
        definition = f"tcp://{self.host}:{self.port}"
        if verbose:
            return f"{definition!r} -> {self.status}"
        else:
            return definition


class PgCheck(Check):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        if "?" in connection_string.rsplit("/", 1)[1]:
            self.separator = "&"
        else:
            self.separator = "?"

    def run(self, options):
        with closing(
            psycopg.connect(f"{self.connection_string}{self.separator}connect_timeout={max(1, int(options.check_timeout))}")
        ) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT version()")
                cur.fetchone()

    def __repr__(self):
        return f"PgCheck({self.connection_string})"

    def display_definition(self, *, verbose_passwords, _password_re=re.compile(r":[^@:]+@")):
        definition = str(self.connection_string)
        if not verbose_passwords:
            definition = _password_re.sub(":******@", definition, 1)
        return definition


class HttpCheck(Check):
    def __init__(self, url):
        self.handlers = []
        self.parsed_url = url = urlparse(url)
        self.scheme = url.scheme
        self.insecure = False
        if url.scheme == "https+insecure":
            self.insecure = True
            url = url._replace(scheme="https")

        if url.port:
            self.netloc = f"{self.hostname}:{self.port}"
        else:
            self.netloc = url.hostname

        cleaned_url = urlunparse(url._replace(netloc=self.netloc))

        if url.username or url.password:
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, cleaned_url, url.username, url.password)
            self.handlers.append(HTTPDigestAuthHandler(passwd=password_mgr))
            self.handlers.append(HTTPBasicAuthHandler(password_mgr=password_mgr))

        self.url = cleaned_url

    def run(self, options):
        handlers = list(self.handlers)
        insecure = self.insecure or options.insecure

        ssl_ctx = ssl.create_default_context()
        if insecure:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        handlers.append(HTTPSHandler(context=ssl_ctx))

        opener = build_opener(*handlers)

        with closing(opener.open(self.url, timeout=options.check_timeout)) as req:
            status = req.getcode()
            if status != 200:
                raise Exception(f"Expected status code 200, got {status!r}")

    def __repr__(self):
        return f"HttpCheck({self.url}, insecure={self.do_insecure}, status={self.status})"

    def display_definition(self, *, verbose_passwords):
        url = self.parsed_url
        if not verbose_passwords:
            if not url.password:
                mask = "******"
            else:
                mask = f"{url.username}:******"
            url = url._replace(netloc=f"{mask}@{self.netloc}")
        return urlunparse(url)


class UnixCheck(Check):
    def __init__(self, path):
        self.path = path

    def run(self, options):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(options.check_timeout)
        with closing(sock):
            sock.connect(self.path)

    def __repr__(self):
        return f"UnixCheck({self.path!r}, status={self.status})"

    def display_definition(self, **_):
        return f"unix://{self.path}"


class PathCheck(Check):
    def __init__(self, path):
        self.path = path

    def run(self, _):
        os.stat(self.path)
        if not os.access(self.path, os.R_OK):
            raise Exception(f"Failed access({self.path!r}, R_OK) test")

    def __repr__(self):
        return f"PathCheck({self.path!r}, status={self.status})"

    def display_definition(self, **_):
        return f"path://{self.path}"


class EvalCheck(Check):
    def __init__(self, expr):
        self.expr = expr
        self.ns = {}
        try:
            tree = ast.parse(expr)
        except SyntaxError as exc:
            raise argparse.ArgumentTypeError(f'Invalid service spec {expr!r}. Parse error:\n  {exc.text} {" " * exc.offset}^\n{exc}')
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if not hasattr(builtins, node.id):
                    try:
                        __import__(node.id)
                    except ImportError as exc:
                        raise argparse.ArgumentTypeError(f"Invalid service spec {expr!r}. Import error: {exc}")
                    self.ns[node.id] = sys.modules[node.id]

    def run(self, _):
        result = eval(self.expr, dict(self.ns), dict(self.ns))
        if not result:
            raise Exception(f"Failed to evaluate {self.expr!r}. Result {result!r} is falsey")

    def __repr__(self):
        return f"EvalCheck({self.expr!r}, ns={self.ns!r}, status={self.status})"

    def display_definition(self, **_):
        return f"eval://{self.expr}"


class AnyCheck(Check):
    def __init__(self, checks):
        self.checks = checks

    def run(self, options):
        for check in self.checks:
            if check.is_passing(options):
                break
        else:
            raise Exception("ALL FAILED")

    def __repr__(self):
        return f'AnyCheck({", ".join(map(repr, self.checks))}, status={self.status})'

    def display(self, *, verbose, **kwargs):
        checks = ", ".join(map(methodcaller("display", verbose=verbose, **kwargs), self.checks))
        if verbose:
            return f"any({checks}) -> {self.status}"
        else:
            return f"any({checks})"


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
            raise argparse.ArgumentTypeError(f"Failed to parse {display_value!r}: {exc}. Must be a valid connection URI.")
        return PgCheck(connection_uri)
    elif proto == "unix":
        return UnixCheck(value)
    elif proto == "path":
        return PathCheck(value)
    elif proto in ("http", "https", "https+insecure"):
        return HttpCheck("%s://%s" % (proto, value))
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
    import holdup

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {holdup.__version__} from {holdup.__file__}",
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
        os.execvp(command[0], command)
