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

    tcp = socket.socket(socket.AF_UNIX)
    if os.path.exists('/tmp/holdup-test.sock'):
        os.unlink('/tmp/holdup-test.sock')
    tcp.bind('/tmp/holdup-test.sock')
    tcp.listen(1)
    result = testdir.run(
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s' % port,
        'unix:///tmp/holdup-test.sock',
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success'])
    t.join()


def test_no_abort(testdir, extra):
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        '-n',
        'tcp://localhost:0',
        'unix:///doesnt/exist',
        *extra
    )
    result.stderr.fnmatch_lines(['Failed checks: tcp://localhost:0 ([[]Errno 111[]]*), unix:///doesnt/exist ([[]Errno 2[]]*)'])
