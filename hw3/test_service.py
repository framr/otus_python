# -*- coding: utf-8 -*-
import pytest
from BaseHTTPServer import HTTPServer
from threading import Thread
import socket
import requests
import json
from collections import namedtuple

from api import MainHTTPHandler, get_store
from kvstore import ZMQKVServer
from scoring import user_key


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("localhost", 0))
    addr, port = s.getsockname()
    s.close()
    return port


@pytest.fixture(scope="module")
def mock_kvstore():
    KVStoreStruct = namedtuple("KVStoreStruct", "client server server_thread port")
    port = get_free_port()
    addr = "tcp://127.0.0.1:{port}".format(port=port)
    server = ZMQKVServer(addr)
    client = get_store(addr=addr)
    server_thread = Thread(target=server.run)
    server_thread.daemon = True
    server_thread.start()
    return KVStoreStruct(client, server, server_thread, port)


@pytest.fixture(scope="module")
def mock_server(mock_kvstore):
    port = get_free_port()
    handler = MainHTTPHandler
    handler.set_store(mock_kvstore.client)
    server = HTTPServer(("localhost", port), handler)
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


@pytest.mark.parametrize("req", [{"a": 1}, {1: 1}, [0], "1"])
def test_422_for_malformed_json(mock_server, req):
    port = mock_server[2]
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 422


def test_404_for_wrong_meth_path(mock_server):
    port = mock_server[2]
    req = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"first_name": "Darth", "last_name": "Vader"}}
    resp = get_response(port, data=json.dumps(req), meth="amethod")
    assert resp.status_code == 404


def test_422_for_bad_method(mock_server):
    port = mock_server[2]
    req = {"account": "horns&hoofs", "login": "h&f", "method": "online_score_XXX", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"first_name": "Darth", "last_name": "Vader"}}
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 422


@pytest.mark.parametrize("arguments", [{"first_name": "Darth"}, {"second_name": "Vader"}, {"phone": u"74953332222"}, {"gender": 2}])
def test_422_for_bad_arguments(mock_server, arguments):
    port = mock_server[2]
    req = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"first_name": "Darth"}}
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 422


def test_403_for_bad_auth(mock_server):
    port = mock_server[2]
    req = {"account": "horns&hoofs", "login": "h&&&&&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"first_name": "Darth", "last_name": "Vader"}}
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 403


######### Test API integration with real kvstore ##########
def test_clients_interests(mock_kvstore, mock_server):
    port = mock_server[2]
    kvstore = mock_kvstore.client
    args = {"client_ids": [1, 2], "date": u"01.01.2018"}

    def key(cid):
        return "i:%s" % cid
    kvstore.set(key(1), json.dumps(("pets", "tv")))
    kvstore.set(key(2), json.dumps(("travel", "music")))
    req = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"clients_interests",
        "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95"}
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 200
    assert json.loads(resp.json()["response"]) == {"1": [u"pets", u"tv"], "2": [u"travel", u"music"]}


def test_online_score(mock_kvstore, mock_server):
    port = mock_server[2]
    kvstore = mock_kvstore.client
    score = 100500
    args = {"first_name": u"Darth", "last_name": u"Vader"}
    key = user_key(first_name=args["first_name"], last_name=args["last_name"])
    kvstore.cache_set(key, score)
    req = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"online_score",
        "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95"}
    resp = get_response(port, data=json.dumps(req))
    assert resp.status_code == 200
    assert json.loads(resp.json()["response"]) == {"score": 100500}
