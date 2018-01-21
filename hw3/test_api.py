#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import hashlib
from datetime import datetime
from scoring import user_key
import json
from cStringIO import StringIO


import api
from api import ClientsInterestsRequest, MethodRequest, OnlineScoreRequest, MainHTTPHandler
from kvstore import Connection, ZMQKVClient, ConnectionError


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"


######### Test Requests classes ###########

@pytest.mark.parametrize("arguments", [{}, {"client_ids": []}])
def test_invalid_clients_interests_empty_fields(arguments):
    meth_req = type("MethodRequest", (object,), {"arguments": arguments})()
    interests = ClientsInterestsRequest(meth_req, {}, {})
    interests.parse_request()
    assert not interests.valid


@pytest.mark.parametrize("arguments", [{"client_ids": [1, 2]}, {"client_ids": [0, 1], "date": u"01.01.2018"}])
def test_clients_interests_ok(arguments):
    meth_req = type("MethodRequest", (object,), {"arguments": arguments})()
    interests = ClientsInterestsRequest(meth_req, {}, {})
    interests.parse_request()
    assert interests.valid


@pytest.mark.parametrize("arguments", [
    {}, {"first_name": u"Hahn"}, {"last_name": u"Banach"}, {"phone": u"74953332222", "first_name": u"Hahn", "gender": 0},
    {"last_name": u"Banach", "email": u"iamhahn@banach.com", "birthday": u"01.01.2018"}
    ])
def test_incomplete_online_score_fields(arguments):
    meth_req = type("MethodRequest", (object,), {"arguments": arguments})()
    interests = OnlineScoreRequest(meth_req, {}, {})
    interests.parse_request()
    assert not interests.valid


@pytest.mark.parametrize("arguments", [
    {"first_name": u"Hahn", "last_name": u"Banach"}, {"phone": u"74953332222", "email": u"iamhahn@banach.com"},
    {"birthday": u"01.01.2018", "gender": 0}
    ])
def test_online_score_fields_ok(arguments):
    meth_req = type("MethodRequest", (object,), {"arguments": arguments})()
    interests = OnlineScoreRequest(meth_req, {}, {})
    interests.parse_request()
    assert interests.valid


#############################
######### Test API ##########
#############################


class TestApi(object):
    def __init__(self):
        self.context = {}
        self.headers = {}
        # self.store = MockKVStore()
    def get_response(self, request, store=None):
        self.context = {}
        return api.method_handler({"body": request, "headers": self.headers}, self.context, store)
    def enforce_valid_token(self, request):
        if request["login"] == ADMIN_LOGIN:
            # XXX: relying on datetime.now() is a bad idea, we should better monkeypatch it
            digest = hashlib.sha512(datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
        else:
            digest = hashlib.sha512(request["account"] + request["login"] + SALT).hexdigest()
        request["token"] = digest.decode("utf-8")


@pytest.fixture
def test_api():
    return TestApi()


@pytest.mark.parametrize("request", [{}])
def test__empty_request(request, test_api):
    _, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize("request", [
    {"account": u"horns&hoofs", "logiiiiin": u"h&f", "token": u"TBD", "arguments": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"h&f", "tokeeeeen": u"TBD", "arguments": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"h&f", "token": u"TBD", "argumeeeeeents": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"h&f", "token": u"TBD", "arguments": {}, "meeeeeethod": u"online_score"},
    {"account": u"horns&hoofs", "token": u"TBD", "arguments": {}, "method": "online_score"},
    ])
def test_invalid_request_bad_arg_name(request, test_api):
    _, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize("request", [
    {"account": 1111, "login": u"h&f", "token": u"TBD", "arguments": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": 1111, "token": u"TBD", "arguments": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"h&f", "token": 11111, "arguments": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"h&f", "token": u"TBD", "arguments": 1111, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"h&f", "token": u"TBD", "arguments": {}, "method": 1111},
    ])
def test_invalid_request_bad_arg_type(request, test_api):
    _, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize("request", [
    {"account": u"horns&hoofs", "login": u"h&f", "token": u"XXX", "arguments": {}, "method": u"online_score"},
    {"account": u"horns&hoofs", "login": u"admin", "token": u"YYY", "arguments": {}, "method": u"online_score"}
    ])
def test_auth_bad(request, test_api):
    msg, code = test_api.get_response(request)
    assert code == api.FORBIDDEN


@pytest.mark.parametrize("request", [
    {"account": u"horns&hoofs", "login": u"h&f", "arguments": {}, "method": u"online_scoreXXX"},
    {"account": u"horns&hoofs", "login": u"admin", "arguments": {}, "method": -1},
    {"account": u"horns&hoofs", "login": u"admin", "arguments": {}, "method": 0},
    ])
def test_invalid_method_name(request, test_api):
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize("arguments", [
    {},
    {"first_name": 0, "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birthday": u"01.01.2018" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvaderyahoo.com", "birthday": u"01.01.2018" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birthday": u"2018.01.01" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birthday": u"01.01.2018" , "gender": 3}
    ])
def test_invalid_score_request(arguments, test_api):
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": arguments, "method": u"online_score"}
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize("arguments", [
    {},
    {"client_ids": [], "date": u"01.01.2018"}
    ])
def test_invalid_clients_interests_request(arguments, test_api):
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": arguments, "method": u"clients_interests"}
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize("arguments", [
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birthday": u"01.01.2018",
    "gender": 0, "phone": u"74993332222"}, {"first_name": u"Hahn", "last_name": u"Banach"},
    {"phone": u"74953332222", "email": u"iamhahn@banach.com"}, {"gender": 2, "birthday": u"01.01.2018"}
    ])
def test_score_request_ok(arguments, test_api):
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": arguments, "method": u"online_score"}    
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    assert code == api.OK
    assert sorted(test_api.context["has"]) == sorted(arguments.keys())


######### Test API integration with kvstore ##########

class MockKVStore(object):
    def __init__(self):
        self._cache = {}
        self._store = {}
    def cache_set(self, key, value, ttl=None):
        self._cache[key] = value
    def cache_get(self, key):
        return self._cache.get(key, None)
    def set(self, key, value):
        self._store[key] = value
    def get(self, key):
        return self._store.get(key, None)


@pytest.fixture()
def kvstore():
    return MockKVStore()


def test_admin_score(request, test_api):
    request = {"account": u"horns&hoofs", "login": u"admin", "arguments": {"first_name": u"Hahn", "last_name": u"Banach"},
               "method": u"online_score"}
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    assert json.loads(msg) == {"score": 42}
 

@pytest.mark.parametrize("score", [0.1, -1.0, 100.0, 1e+6])
def test_return_score_from_store_cache(score, kvstore, test_api):
    args = {"first_name": u"Darth", "last_name": u"Vader"}
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"online_score"}    
    key = user_key(first_name=args["first_name"], last_name=args["last_name"])
    kvstore.cache_set(key, score)
    test_api.enforce_valid_token(request)
    res, _ = test_api.get_response(request, store=kvstore)
    assert json.loads(res) == {"score": score}


@pytest.mark.parametrize("score", [0.1, -1.0, 100.0, 1e+6])
def test_return_score_from_store_cache_utf8_rus_name(score, kvstore, test_api):
    args = {"first_name": u"Дарт", "last_name": u"Вэйдер"}
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"online_score"}    
    key = user_key(first_name=args["first_name"], last_name=args["last_name"])
    kvstore.cache_set(key, score)
    test_api.enforce_valid_token(request)
    res, _ = test_api.get_response(request, store=kvstore)
    assert json.loads(res) == {"score": score}


def test_clients_interests_request_returns_valid_interests(kvstore, test_api): 
    args = {"client_ids": [1, 2], "date": u"01.01.2018"}
    def key(cid):
        return "i:%s" % cid
    kvstore.set(key(1), json.dumps(("pets", "tv")))
    kvstore.set(key(2), json.dumps(("travel", "music")))
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"clients_interests"}
    test_api.enforce_valid_token(request)
 
    msg, code = test_api.get_response(request, store=kvstore)
    data = json.loads(msg)
    assert data == {"1": [u"pets", u"tv"], "2": [u"travel", u"music"]}


def test_clients_interests_request_returns_valid_interests_utf8_rus_interests(kvstore, test_api): 
    args = {"client_ids": [1, 2], "date": u"01.01.2018"}
    def key(cid):
        return "i:%s" % cid
    kvstore.set(key(1), json.dumps(("котики", "единороги")))
    kvstore.set(key(2), json.dumps(("митал", "гитары")))
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"clients_interests"}
    test_api.enforce_valid_token(request)
 
    msg, code = test_api.get_response(request, store=kvstore)
    data = json.loads(msg)
    assert data == {"1": [u"котики", u"единороги"], "2": [u"митал", u"гитары"]}


def test_clients_interests_request_returns_valid_interests(kvstore, test_api): 
    args = {"client_ids": [1, 2], "date": u"01.01.2018"}
    def key(cid):
        return "i:%s" % cid
    kvstore.set(key(1), json.dumps(("pets", "tv")))
    kvstore.set(key(2), json.dumps(("travel", "music")))
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"clients_interests"}
    test_api.enforce_valid_token(request)
 
    msg, code = test_api.get_response(request, store=kvstore)
    data = json.loads(msg)
    assert data == {"1": [u"pets", u"tv"], "2": [u"travel", u"music"]}


def test_clients_interests_request_ok(kvstore, test_api): 
    args = {"client_ids": [1, 2], "date": u"01.01.2018"}
    def key(cid):
        return "i:%s" % cid
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"clients_interests"}
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request, store=kvstore)
    assert code == api.OK 
    assert test_api.context == {"nclients": 2}


######### Test behaviour when kvstore connection fails ##########

@pytest.fixture()
def bad_kvstore():
    class BadConnection(Connection):
        def init_connection(self):
            return self
        def send(data):
            raise ConnectionError("Network Error")
    return ZMQKVClient(connection_cls=BadConnection)


@pytest.mark.parametrize("score", [0.1, -1.0, 100.0, 1e+6])
def test_return_score_cache_unavailable(score, bad_kvstore, test_api):
    args = {"first_name": u"Darth", "last_name": u"Vader"}
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"online_score"}    
    key = user_key(first_name=args["first_name"], last_name=args["last_name"])
    test_api.enforce_valid_token(request)
    res, code  = test_api.get_response(request, store=bad_kvstore)
    assert code == api.OK


def test__clients_interests_store_unavailable_raises(bad_kvstore, test_api): 
    args = {"client_ids": [1, 2], "date": u"01.01.2018"}
    def key(cid):
        return "i:%s" % cid
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"clients_interests"}
    test_api.enforce_valid_token(request)
    with pytest.raises(Exception):
        _, _ = test_api.get_response(request, store=bad_kvstore)


######### Test MainHTTPHandler ##########

class TestMainHTTPHandler(MainHTTPHandler):
    def __init__(self):
        pass
    def method_handler(self):
        pass
    def setup(self):
        self.headers = {"Content-Length": 0}
        self.rfile = StringIO()
        self.wfile = StringIO()
        self.path = ""
        self.router = {"method": self.method_handler}
        return self
    def finish(self):
        self.rfile.close()
        self.wfile.close()
    def send_response(self, code):
        pass
    def send_header(self, key, value):
        pass
    def end_headers(self):
        pass

@pytest.fixture()
def httphandler():
    return TestMainHTTPHandler().setup()


def test_400_for_malformed_json(httphandler):
    data = "XXX%s" % json.dumps({})
    httphandler.rfile.write(data)
    httphandler.rfile.seek(0)
    httphandler.headers["Content-Length"] = len(data)
    httphandler.do_POST()
    response = json.loads(httphandler.wfile.getvalue())
    assert response["code"] == 400


def test_404_for_bad_method(httphandler):
    data = "%s" % json.dumps({"id": 1})
    httphandler.rfile.write(data)
    httphandler.rfile.seek(0)
    httphandler.headers["Content-Length"] = len(data)
    httphandler.path = "mypath"
    httphandler.do_POST()
    response = json.loads(httphandler.wfile.getvalue())
    assert response["code"] == 404


def test_request_response_routing(httphandler):
    args = {"first_name": u"Darth", "last_name": u"Vader"}
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"online_score"}
    data = json.dumps(request)
    httphandler.rfile.write(data)
    httphandler.rfile.seek(0)
    httphandler.headers["Content-Length"] = len(data)
    httphandler.path = "method"
    def method_handler(request, ctx, store):
        return json.dumps(request), 200
    httphandler.router = {"method": method_handler}
    httphandler.do_POST()
    response = json.loads(httphandler.wfile.getvalue())
    assert json.loads(response["response"])["body"] == request
    assert response["code"] == 200


def test_500_for_handler_exception(httphandler):
    args = {"first_name": u"Darth", "last_name": u"Vader"}
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": args, "method": u"online_score"}
    data = json.dumps(request)
    httphandler.rfile.write(data)
    httphandler.rfile.seek(0)
    httphandler.headers["Content-Length"] = len(data)
    httphandler.path = "method"
    def method_handler(request, ctx, store):
        raise ValueError
    httphandler.router = {"method": method_handler}
    httphandler.do_POST()
    response = json.loads(httphandler.wfile.getvalue())
    assert response["code"] == 500
