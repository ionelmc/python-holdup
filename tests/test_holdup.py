import os
import socket
import ssl
import threading
from distutils import spawn

import pytest

try:
    from inspect import getfullargspec as getargspec
except ImportError:
    from inspect import getargspec

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

pytest_plugins = 'pytester',


def has_urlopen_ssl_context():
    if hasattr(ssl, 'create_default_context'):
        urlopen_argspec = getargspec(urlopen)
        urlopen_args = urlopen_argspec.args
        if hasattr(urlopen_argspec, 'kwonlyargs'):
            urlopen_args.extend(urlopen_argspec.kwonlyargs)
        if 'context' in urlopen_args:
            return True


def has_docker():
    return spawn.find_executable('docker') and spawn.find_executable('docker-compose')


@pytest.fixture(params=[[], ['--', 'python', '-c', 'print("success !")']])
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
        result.stdout.fnmatch_lines(['success !'])
    assert result.ret == 0
    t.join()


@pytest.mark.parametrize('status', [200, 404])
@pytest.mark.parametrize('proto', ['http', 'https'])
def test_http(testdir, extra, status, proto):
    result = testdir.run(
        'holdup',
        '-T', '5',
        '-t', '5.1',
        '%s://httpbin.org/status/%s' % (proto, status),
        *extra
    )
    if extra:
        if status == 200:
            result.stdout.fnmatch_lines(['success !'])
        else:
            result.stderr.fnmatch_lines(['*HTTP Error 404*'])


@pytest.mark.skipif('not has_urlopen_ssl_context()')
def test_http_insecure_with_option(testdir):
    result = testdir.run(
        'holdup',
        '-t', '2',
        '--insecure',
        'https://self-signed.badssl.com/',
    )
    assert result.ret == 0


@pytest.mark.skipif('not has_urlopen_ssl_context()')
def test_http_insecure_with_proto(testdir):
    result = testdir.run(
        'holdup',
        '-t', '2',
        'https+insecure://self-signed.badssl.com/',
    )
    assert result.ret == 0


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
        '-v',
        '-t', '0.5',
        'tcp://localhost:%s/,path:///tmp/holdup-test,unix:///tmp/holdup-test.sock' % port,
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines([
            "holdup: Waiting for 0.5s (0.5s per check, 0.2s sleep between loops) for these services: "
            "any('tcp://localhost:*', 'path:///tmp/holdup-test', 'unix:///tmp/holdup-test.sock')",
            "holdup: Passed check: 'path:///tmp/holdup-test' (PASSED)",
            "holdup: Passed check: any('tcp://localhost:*' (*), 'path:///tmp/holdup-test' (PASSED), "
            "'unix:///tmp/holdup-test.sock' (PENDING)) (PASSED)",
            "holdup: Executing: python -c 'print(\"success !\")'",
            "success !",
        ])
    assert result.ret == 0


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
        result.stdout.fnmatch_lines(['success !'])
    assert result.ret == 0
    t.join()


def test_any_failed(testdir):
    tcp = socket.socket()
    tcp.bind(('127.0.0.1', 0))
    _, port = tcp.getsockname()

    result = testdir.run(
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s/,path:///doesnt/exist,unix:///doesnt/exist' % port
    )
    result.stderr.fnmatch_lines([
        "holdup: Failed checks: any('tcp://localhost:%s' (*), 'path:///doesnt/exist' (*), "
        "'unix:///doesnt/exist' (*)) (No checks passed). "
        "Aborting!" % port,
    ])


def test_no_abort(testdir, extra):
    result = testdir.run(
        'holdup',
        '-t',
        '0.1', '-n',
        'tcp://localhost:0',
        'tcp://localhost:0/',
        'path:///doesnt/exist',
        'unix:///doesnt/exist',
        *extra
    )
    result.stderr.fnmatch_lines([
        "holdup: Failed checks: 'tcp://localhost:0' (*), "
        "'path:///doesnt/exist' (*), 'unix:///doesnt/exist' (*). "
        "Treating as success because of --no-abort.",
    ])


@pytest.mark.skipif(os.path.exists('/.dockerenv'), reason='chmod(0) does not work in docker')
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
    result.stderr.fnmatch_lines([
        "holdup: Failed checks: 'path://%s' (Failed access('%s', R_OK) test). "
        "Treating as success because of --no-abort." % (foobar, foobar),
    ])


def test_bad_timeout(testdir):
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        '-T', '2',
        'path:///',
    )
    result.stderr.fnmatch_lines([
        '*error: --timeout value must be greater than --check-timeout value!'
    ])


def test_eval_bad_import(testdir):
    result = testdir.run(
        'holdup',
        'eval://foobar123.foo()',
    )
    result.stderr.fnmatch_lines([
        "*error: argument service: Invalid service spec 'foobar123.foo()'. Import error: No module named*",
    ])


def test_eval_bad_expr(testdir):
    result = testdir.run(
        'holdup',
        'eval://foobar123.foo(.)',
    )
    result.stderr.fnmatch_lines([
        "*error: argument service: Invalid service spec 'foobar123.foo(.)'. Parse error:",
        "  foobar123.foo(.)",
        "*               ^",
        "invalid syntax (<unknown>, line 1)",
    ])


def test_eval_falsey(testdir):
    result = testdir.run(
        'holdup',
        '-t', '0',
        'eval://None'
    )
    result.stderr.fnmatch_lines([
        "holdup: Failed checks: 'eval://None' (Failed to evaluate 'None'. Result None is falsey). Aborting!"
    ])
    assert result.ret == 1


def test_eval_distutils(testdir, extra):
    result = testdir.run(
        'holdup',
        'eval://__import__("distutils.spawn").spawn.find_executable("find")',
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success !'])
    assert result.ret == 0


def test_eval_comma(testdir, extra):
    result = testdir.run(
        'holdup',
        'eval://os.path.join("foo", "bar")',
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success !'])
    assert result.ret == 0


def test_eval_comma_anycheck(testdir, extra):
    result = testdir.run(
        'holdup',
        'path://whatever123,eval://os.path.join("foo", "bar")',
        *extra
    )
    if extra:
        result.stdout.fnmatch_lines(['success !'])
    assert result.ret == 0


@pytest.mark.parametrize('proto', ['postgresql', 'postgres', 'pg'])
def test_pg_timeout(testdir, proto):
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        proto + '://0.0.0.0/foo'
    )
    result.stderr.fnmatch_lines([
        "holdup: Failed checks: 'postgresql://0.0.0.0/foo' (*",
    ])


@pytest.mark.parametrize('proto', ['postgresql', 'postgres', 'pg'])
def test_pg_unavailable(testdir, proto):
    testdir.tmpdir.join('psycopg2cffi').ensure(dir=1)
    testdir.tmpdir.join('psycopg2cffi/__init__.py').write('raise ImportError("Disabled for testing")')
    testdir.tmpdir.join('psycopg2').ensure(dir=1)
    testdir.tmpdir.join('psycopg2/__init__.py').write('raise ImportError("Disabled for testing")')
    result = testdir.run(
        'holdup',
        '-t', '0.1',
        proto + ':///'
    )
    result.stderr.fnmatch_lines([
        'holdup: error: argument service: Protocol %s unusable. Install holdup[[]pg[]].' % proto,
    ])


@pytest.fixture
def testdir2(testdir):
    os.chdir(os.path.dirname(__file__))
    testdir.tmpdir.join('stderr').mksymlinkto(testdir.tmpdir.join('stdout'))
    yield testdir


@pytest.mark.skipif("not has_docker()")
def test_func_pg(testdir2):
    result = testdir2.run(
        './test_pg.sh',
        'holdup', 'pg://app:app@pg/app', '--',
    )
    result.stdout.fnmatch_lines(['success !'])
    assert result.ret == 0


@pytest.mark.skipif("not has_docker()")
def test_func_pg_tcp_service_failure(testdir2):
    result = testdir2.run(
        './test_pg.sh',
        'holdup', 'tcp://pg:5432',
        '-T', '0.01',
        '-i', '0',
        '-t', '10',
        '-v',
        '--',
    )
    assert result.ret == 1
