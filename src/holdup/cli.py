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
from __future__ import print_function

import argparse
import os
import socket
import sys
from contextlib import closing
from time import time


class TcpCheck(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __call__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        with closing(sock):
            return sock.connect_ex((self.host, self.port)) == 0

    def __str__(self):
        return 'tcp://{0.host}:{0.port}'.format(self)


class UnixCheck(object):
    def __init__(self, path):
        self.path = path

    def __call__(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        with closing(sock):
            return sock.connect_ex(self.path) == 0

    def __str__(self):
        return 'unix://{0.path}'.format(self)


def parse_service(service):
    if '://' not in service:
        raise argparse.ArgumentTypeError('Invalid service spec %r. Must have "://".' % service)
    proto, value = service.split('://', 1)

    if proto == 'tcp':
        if ':' not in value:
            raise argparse.ArgumentTypeError('Invalid service spec %r. Must have ":". Where\'s the port?' % service)
        host, port = value.strip('/').split(':', 1)
        if not port.isdigit():
            raise argparse.ArgumentTypeError('Invalid service spec %r. Port must be a number.' % service)
        port = int(port)
        return TcpCheck(host, port)
    elif proto == 'unix':
        return UnixCheck(value)
    else:
        raise argparse.ArgumentTypeError('Unknown protocol in %r. Must be "tcp" or "unix".' % service)


def filter_passing(checks):
    for check in checks:
        try:
            if not check():
                yield check
        except Exception as exc:
            print(check, exc)
            yield check


parser = argparse.ArgumentParser(
    usage='%(prog)s [-h] [-t SECONDS] [-n] service [service ...] [-- command [arg [arg ...]]]',
    description="Wait for services to be ready and optionally exec command."
)
parser.add_argument('service', nargs=argparse.ONE_OR_MORE, type=parse_service,
                    help='A service to wait for. '
                         'Supported protocols: "tcp://host:port/", "unix:///path/to/domain.sock".')
parser.add_argument('command', nargs=argparse.OPTIONAL,
                    help='An optional command to exec.')
parser.add_argument('-t', '--timeout', metavar='SECONDS', type=float, default=5.0,
                    help='Time to wait for services to be ready. Default: %(default)s')
parser.add_argument('-n', '--no-abort', action='store_true',
                    help='Ignore failed services. '
                         'This makes `holdup` return 0 exit code regardless of services actually responding.')


def main():
    """
    Args:
        argv (list): List of arguments

    Returns:
        int: A return code

    Does stuff.
    """
    if '--' in sys.argv:
        pos = sys.argv.index('--')
        argv, command = sys.argv[1:pos], sys.argv[pos + 1:]
    else:
        argv, command = sys.argv[1:], None
    options = parser.parse_args(args=argv)
    pending = list(options.service)
    start = time()
    while pending and time() - start < options.timeout:
        pending = list(filter_passing(pending))
    if pending:
        if options.no_abort:
            print('Failed checks:', ', '.join(str(check) for check in pending), file=sys.stderr)
        else:
            parser.exit(1, 'Failed service checks: %s. Aborting!\n' % ', '.join(str(check) for check in pending))
    if command:
        os.execvp(command[0], command)
