import os
import socket
import sys
import threading

from holdup.cli import main


def test_main(monkeypatch):
    tcp = socket.socket()
    tcp.bind(('127.0.0.1', 0))
    tcp.listen(1)
    _, port = tcp.getsockname()
    t = threading.Thread(target=tcp.accept).start()

    tcp = socket.socket(socket.AF_UNIX)
    if os.path.exists('/tmp/holdup-test.sock'):
        os.unlink('/tmp/holdup-test.sock')
    tcp.bind('/tmp/holdup-test.sock')
    tcp.listen(1)
    monkeypatch.setattr(sys, 'argv', [
        'holdup',
        '-t', '0.5',
        'tcp://localhost:%s' % port,
        'unix:///tmp/holdup-test.sock',
        '--',
        'python', '-c', 'print("success")'
    ])
    main()

    monkeypatch.setattr(sys, 'argv', [
        'holdup',
        '-t', '0.1',
        '-n',
        'tcp://localhost:0',
        'unix:///doesnt/exist',
        '--',
        'python', '-c', 'print("success")'
    ])
    main()

    t.join()
