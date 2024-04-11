import argparse
import ast
import builtins
import os
import re
import socket
import ssl
import sys
from contextlib import closing
from operator import methodcaller
from urllib.parse import urlparse
from urllib.parse import urlunparse
from urllib.request import HTTPBasicAuthHandler
from urllib.request import HTTPDigestAuthHandler
from urllib.request import HTTPPasswordMgrWithDefaultRealm
from urllib.request import HTTPSHandler
from urllib.request import Request
from urllib.request import build_opener

from . import __version__
from .pg import psycopg


class Check:
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
            self.netloc = f"{url.hostname}:{url.port}"
        else:
            self.netloc = url.hostname
        self.host = url.hostname

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
        opener.addheaders = [("User-Agent", f"python-holdup/{__version__}")]
        request = Request(self.url, headers={"Host": self.host})  # noqa: S310
        with closing(opener.open(request, timeout=options.check_timeout)) as req:
            status = req.getcode()
            if status != 200:
                raise Exception(f"Expected status code 200, got {status!r}")

    def __repr__(self):
        return f"HttpCheck({self.url}, insecure={self.insecure}, status={self.status})"

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
        # necessary to check if it exists.
        os.stat(self.path)  # noqa: PTH116
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
            raise argparse.ArgumentTypeError(
                f'Invalid service spec {expr!r}. Parse error:\n  {exc.text} {" " * exc.offset}^\n{exc}'
            ) from None
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if not hasattr(builtins, node.id):
                    try:
                        __import__(node.id)
                    except ImportError as exc:
                        raise argparse.ArgumentTypeError(f"Invalid service spec {expr!r}. Import error: {exc}") from None
                    self.ns[node.id] = sys.modules[node.id]

    def run(self, _):
        result = eval(self.expr, dict(self.ns), dict(self.ns))  # noqa: S307
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
