import os
import socket
import threading

import pytest

pytest_plugins = 'pytester',


@pytest.fixture(params=[[], ['--', 'python', '-c', 'print("success")']])
def extra(request):
    return request.param


def test_normal(testdir, extra):
    tcp = socket.socket()
    tcp.bind(('127.0.0.1', 0))
    tcp.listen(1)
    _, port = tcp.getsockname()
    t = threading.Thread(target=tcp.accept)
    t.start()

    uds = socket.socket(socket.AF_UNIX)
    if os.path.exists('/tmp/holdup-test.sock'):
        os.unlink('/tmp/holdup-test.sock')
    with open('/tmp/holdup-test', 'w'):
        pass
    uds.bind('/tmp/holdup-test.sock')
    uds.listen(1)
    result = testdir.run(
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s/' % port,
        'path:///tmp/holdup-test',
        'unix:///tmp/holdup-test.sock',
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success'])
    t.join()


@pytest.mark.parametrize('status', [200, 404])
@pytest.mark.parametrize('proto', ['http', 'https'])
def test_http(testdir, extra, status, proto):
    result = testdir.run(
        'holdup',
        '-T', '5',
        '%s://httpbin.org/status/%s' % (proto, status),
        *extra
    )
    if extra:
        if status == 200:
            result.stdout.fnmatch_lines(['success'])
        else:
            result.stderr.fnmatch_lines(['*HTTP Error 404*'])


def test_any(testdir, extra):
    tcp = socket.socket()
    tcp.bind(('127.0.0.1', 0))
    _, port = tcp.getsockname()

    uds = socket.socket(socket.AF_UNIX)
    if os.path.exists('/tmp/holdup-test.sock'):
        os.unlink('/tmp/holdup-test.sock')
    uds.bind('/tmp/holdup-test.sock')
    uds.listen(1)
    result = testdir.run(
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s/,path:///tmp/holdup-test,unix:///tmp/holdup-test.sock' % port,
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success'])


def test_any_same_proto(testdir, extra):
    tcp1 = socket.socket()
    tcp1.bind(('127.0.0.1', 0))
    _, port1 = tcp1.getsockname()

    tcp2 = socket.socket()
    tcp2.bind(('127.0.0.1', 0))
    tcp2.listen(1)
    _, port2 = tcp2.getsockname()
    t = threading.Thread(target=tcp2.accept)
    t.start()

    result = testdir.run(
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s,localhost:%s/' % (port1, port2),
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success'])
    t.join()


def test_any_failed(testdir):
    tcp = socket.socket()
    tcp.bind(('127.0.0.1', 0))
    _, port = tcp.getsockname()

    result = testdir.run(
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s/,path:///doesnt/exist,unix:///doesnt/exist' % port,
    )
    result.stderr.fnmatch_lines([
        'Failed service checks: any(tcp://localhost:%s,path:///doesnt/exist,unix:///doesnt/exist) '
        '(Nothing succeeded: '
        'tcp://localhost:%s ([[]Errno 111[]]*), '
        'path:///doesnt/exist ([[]Errno 2[]]*), '
        'unix:///doesnt/exist ([[]Errno 2[]]*). Aborting!' % (port, port)
    ])


def test_no_abort(testdir, extra):
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        '-n',
        'tcp://localhost:0',
        'tcp://localhost:0/',
        'path:///doesnt/exist',
        'unix:///doesnt/exist',
        *extra
    )
    result.stderr.fnmatch_lines([
        'Failed checks: tcp://localhost:0 ([[]Errno 111[]]*), '
        'path:///doesnt/exist ([[]Errno 2[]]*), unix:///doesnt/exist ([[]Errno 2[]]*)'
    ])


def test_not_readable(testdir, extra):
    foobar = testdir.maketxtfile(foobar='')
    foobar.chmod(0)
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        '-n',
        'path://%s' % foobar,
        *extra
    )
    result.stderr.fnmatch_lines(["Failed checks: path://%s (Failed access('%s', 'R_OK') test.)" % (foobar, foobar)])


def test_bad_timeout(testdir):
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        '-T', '2',
        'path:///'
    )
    result.stderr.fnmatch_lines([
        '*error: --timeout value must be greater than --check-timeout value!'
    ])
