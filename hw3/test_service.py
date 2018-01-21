# -*- coding: utf-8 -*-
import pytest
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import socket
import requests
import json

from api import MainHTTPHandler


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("localhost", 0))
    addr, port = s.getsockname()
    s.close()
    return port


@pytest.fixture(scope="module")
def mock_server():
    port = get_free_port()
    server = HTTPServer(("localhost", port), MainHTTPHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server, server_thread, port


def get_response(port, data=None, meth="method"):
    r = requests.post("http://localhost:{port}/{meth}/".format(port=port, meth=meth), data=data or {})
    return r


def test_200_for_valid_online_score_meth(mock_server):
    port = mock_server[2]
    req = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"first_name": "Darth", "last_name": "Vader"}}
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 200
