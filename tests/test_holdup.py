# ruff: noqa: PTH110, PTH120, PTH123
import os
import shutil
import socket
import threading

import pytest

pytest_plugins = ("pytester",)


def has_docker():
    return shutil.which("docker")


@pytest.fixture(params=[[], ["--", "python", "-c", 'print("success !")']])
def extra(request):
    return request.param


def test_normal(testdir, tmp_path_factory, extra):
    tcp = socket.socket()
    tcp.bind(("127.0.0.1", 0))
    tcp.listen(1)
    _, port = tcp.getsockname()

    def accept():
        conn, _ = tcp.accept()
        conn.close()

    t = threading.Thread(target=accept)
    t.start()

    uds = socket.socket(socket.AF_UNIX)

    tmp_path = tmp_path_factory.getbasetemp()
    unix_path = tmp_path / "sock"
    path_path = tmp_path / "file"

    with open(path_path, "w"):
        pass
    uds.bind(str(unix_path))
    uds.listen(1)

    result = testdir.run("holdup", "-t", "0.5", f"tcp://localhost:{port}/", f"path://{path_path}", f"unix://{unix_path}", *extra)
    if extra:
        result.stdout.fnmatch_lines(["success !"])
    assert result.ret == 0
    t.join()
    uds.close()
    tcp.close()
    unix_path.unlink()


@pytest.mark.parametrize("status", [200, 404])
@pytest.mark.parametrize("proto", ["http", "https"])
def test_http(testdir, extra, status, proto):
    result = testdir.run("holdup", "-T", "5", "-t", "5.1", f"{proto}://httpbingo.org/status/{status}", *extra)
    if extra:
        if status == 200:
            result.stdout.fnmatch_lines(["success !"])
        else:
            result.stderr.fnmatch_lines(["*HTTP Error 404*"])


@pytest.mark.parametrize("status", [200, 404])
def test_http_port(testdir, extra, status):
    result = testdir.run("holdup", "-T", "5", "-t", "5.1", f"http://httpbingo.org:80/status/{status}", *extra)
    if extra:
        if status == 200:
            result.stdout.fnmatch_lines(["success !"])
        else:
            result.stderr.fnmatch_lines(["*HTTP Error 404*"])


@pytest.mark.parametrize("auth", ["basic-auth", "digest-auth/auth"])
@pytest.mark.parametrize("proto", ["http", "https"])
def test_http_auth(testdir, extra, auth, proto):
    result = testdir.run("holdup", "-T", "5", "-t", "5.1", f"{proto}://usr:pwd@httpbingo.org/{auth}/usr/pwd", *extra)
    if extra:
        result.stdout.fnmatch_lines(["success !"])


def test_http_insecure_with_option(testdir):
    result = testdir.run("holdup", "-t", "2", "--insecure", "https://self-signed.badssl.com/")
    assert result.ret == 0


def test_http_insecure_with_proto(testdir):
    result = testdir.run("holdup", "-t", "2", "https+insecure://self-signed.badssl.com/")
    assert result.ret == 0


def test_any1(testdir, tmp_path_factory, extra):
    tcp = socket.socket()
    tcp.bind(("127.0.0.1", 0))
    _, port = tcp.getsockname()

    uds = socket.socket(socket.AF_UNIX)

    tmp_path = tmp_path_factory.getbasetemp()
    unix_path = tmp_path / "s"
    path_path = tmp_path / "miss"
    uds.bind(str(unix_path))
    uds.listen(1)
    result = testdir.run("holdup", "-v", "-t", "0.5", f"tcp://localhost:{port}/,path://{path_path},unix://{unix_path}", *extra)
    if extra:
        result.stdout.fnmatch_lines(
            [
                "holdup: Waiting for 0.5s (0.5s per check, 0.2s sleep between loops) for these services: "
                f"any(tcp://localhost:*, path://{path_path}, unix://{unix_path})",
                f"holdup: Passed check: 'unix://{unix_path}' -> PASSED",
                f"holdup: Passed check: any('tcp://localhost:*' -> *, 'path://{path_path}' ->"
                f" [[]Errno 2[]] No such file or directory: *, "
                f"'unix://{unix_path}' -> PASSED) -> PASSED",
                "holdup: Executing: python -c 'print(\"success !\")'",
                "success !",
            ]
        )
    assert result.ret == 0
    tcp.close()
    uds.close()
    unix_path.unlink()


def test_any2(testdir, tmp_path, extra):
    tcp = socket.socket()
    tcp.bind(("127.0.0.1", 0))
    _, port = tcp.getsockname()

    uds = socket.socket(socket.AF_UNIX)
    unix_path = tmp_path / "s"
    path_path = tmp_path / "miss"
    uds.bind(str(unix_path))
    uds.listen(1)
    result = testdir.run("holdup", "-v", "-t", "0.5", f"path://{path_path},unix://{unix_path},tcp://localhost:{port}/", *extra)
    if extra:
        result.stdout.fnmatch_lines(
            [
                "holdup: Waiting for 0.5s (0.5s per check, 0.2s sleep between loops) for these services: "
                f"any(path://{path_path}, unix://{unix_path}, tcp://localhost:*)",
                f"holdup: Passed check: 'unix://{unix_path}' -> PASSED",
                f"holdup: Passed check: any('path://{path_path}' -> [[]Errno 2[]] No such file or directory: *, "
                f"'unix://{unix_path}' -> PASSED, 'tcp://localhost:*' -> PENDING) -> PASSED",
                "holdup: Executing: python -c 'print(\"success !\")'",
                "success !",
            ]
        )
    assert result.ret == 0
    tcp.close()
    uds.close()
    unix_path.unlink()


def test_any_same_proto(testdir, extra):
    tcp1 = socket.socket()
    tcp1.bind(("127.0.0.1", 0))
    _, port1 = tcp1.getsockname()

    tcp2 = socket.socket()
    tcp2.bind(("127.0.0.1", 0))
    tcp2.listen(1)
    _, port2 = tcp2.getsockname()

    def accept():
        conn, _ = tcp2.accept()
        conn.close()

    t = threading.Thread(target=accept)
    t.start()

    result = testdir.run("holdup", "-t", "0.5", f"tcp://localhost:{port1},localhost:{port2}/", *extra)
    if extra:
        result.stdout.fnmatch_lines(["success !"])
    assert result.ret == 0
    t.join()
    tcp1.close()
    tcp2.close()


def test_any_failed(testdir):
    tcp = socket.socket()
    tcp.bind(("127.0.0.1", 0))
    _, port = tcp.getsockname()

    result = testdir.run("holdup", "-t", "0.5", "tcp://localhost:%s/,path:///doesnt/exist,unix:///doesnt/exist" % port)
    result.stderr.fnmatch_lines(
        [
            "holdup: Failed checks: any('tcp://localhost:%s' -> *, 'path:///doesnt/exist' -> *, "
            "'unix:///doesnt/exist' -> *) -> ALL FAILED. "
            "Aborting!" % port,
        ]
    )
    tcp.close()


def test_no_abort(testdir, extra):
    result = testdir.run(
        "holdup", "-t", "0.1", "-n", "tcp://localhost:0", "tcp://localhost:0/", "path:///doesnt/exist", "unix:///doesnt/exist", *extra
    )
    result.stderr.fnmatch_lines(
        [
            "holdup: Failed checks: 'tcp://localhost:0' -> *, "
            "'path:///doesnt/exist' -> *, 'unix:///doesnt/exist' -> *. "
            "Treating as success because of --no-abort.",
        ]
    )


@pytest.mark.skipif(os.path.exists("/.dockerenv"), reason="chmod(0) does not work in docker")
def test_not_readable(testdir, extra):
    foobar = testdir.maketxtfile(foobar="")
    foobar.chmod(0)
    result = testdir.run("holdup", "-t", "0.1", "-n", "path://%s" % foobar, *extra)
    result.stderr.fnmatch_lines(
        [
            f"holdup: Failed checks: 'path://{foobar}' -> Failed access('{foobar}', R_OK) test. "
            "Treating as success because of --no-abort.",
        ]
    )


def test_bad_timeout(testdir):
    result = testdir.run("holdup", "-t", "0.1", "-T", "2", "path:///")
    result.stderr.fnmatch_lines(["*error: --timeout value must be greater than --check-timeout value!"])


def test_eval_bad_import(testdir):
    result = testdir.run("holdup", "eval://foobar123.foo()")
    result.stderr.fnmatch_lines(
        [
            "*error: argument service: Invalid service spec 'foobar123.foo()'. Import error: No module named*",
        ]
    )


def test_eval_bad_expr(testdir):
    result = testdir.run("holdup", "eval://foobar123.foo(.)")
    result.stderr.fnmatch_lines(
        [
            "*error: argument service: Invalid service spec 'foobar123.foo(.)'. Parse error:",
            "  foobar123.foo(.)",
            "*               ^",
            "invalid syntax (<unknown>, line 1)",
        ]
    )


def test_eval_falsey(testdir):
    result = testdir.run("holdup", "-t", "0", "eval://None")
    result.stderr.fnmatch_lines(["holdup: Failed checks: 'eval://None' -> Failed to evaluate 'None'. Result None is falsey. Aborting!"])
    assert result.ret == 1


def test_eval_distutils(testdir, extra):
    result = testdir.run("holdup", 'eval://__import__("shutil").which("find")', *extra)
    if extra:
        result.stdout.fnmatch_lines(["success !"])
    assert result.ret == 0


def test_eval_comma(testdir, extra):
    result = testdir.run("holdup", 'eval://os.path.join("foo", "bar")', *extra)
    if extra:
        result.stdout.fnmatch_lines(["success !"])
    assert result.ret == 0


def test_eval_comma_anycheck(testdir, extra):
    result = testdir.run("holdup", 'path://whatever123,eval://os.path.join("foo", "bar")', *extra)
    if extra:
        result.stdout.fnmatch_lines(["success !"])
    assert result.ret == 0


@pytest.mark.parametrize("proto", ["postgresql", "postgres", "pg"])
def test_pg_timeout(testdir, proto):
    result = testdir.run("holdup", "-t", "0.1", proto + "://0.0.0.0/foo")
    result.stderr.fnmatch_lines(
        [
            "holdup: Failed checks: 'postgresql://0.0.0.0/foo' -> *",
        ]
    )


@pytest.mark.parametrize("proto", ["postgresql", "postgres", "pg"])
def test_pg_unavailable(testdir, proto):
    testdir.tmpdir.join("psycopg2cffi").ensure(dir=1)
    testdir.tmpdir.join("psycopg2cffi/__init__.py").write('raise ImportError("Disabled for testing")')
    testdir.tmpdir.join("psycopg2").ensure(dir=1)
    testdir.tmpdir.join("psycopg2/__init__.py").write('raise ImportError("Disabled for testing")')
    testdir.tmpdir.join("psycopg").ensure(dir=1)
    testdir.tmpdir.join("psycopg/__init__.py").write('raise ImportError("Disabled for testing")')
    result = testdir.run("holdup", "-t", "0.1", proto + ":///")
    result.stderr.fnmatch_lines(
        [
            "holdup: error: argument service: Protocol %s unusable. Install holdup[[]pg[]]." % proto,
        ]
    )


@pytest.fixture
def testdir2(testdir):
    os.chdir(os.path.dirname(__file__))
    testdir.tmpdir.join("stderr").mksymlinkto(testdir.tmpdir.join("stdout"))
    return testdir


@pytest.mark.skipif("not has_docker()")
def test_func_pg(testdir2):
    result = testdir2.run("./test_pg.sh", "holdup", "pg://app:app@pg/app", "--")
    result.stdout.fnmatch_lines(["success !"])
    assert result.ret == 0


@pytest.mark.skipif("not has_docker()")
def test_func_pg_tcp_service_failure(testdir2):
    # test that the tcp check is worse than the pg check
    result = testdir2.run("./test_pg.sh", "holdup", "tcp://pg:5432", "-T", "0.001", "-i", "0", "-t", "1", "-v", "--")
    assert result.ret == 1
