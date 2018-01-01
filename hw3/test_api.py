#!/usr/bin/env python
import pytest
import api
from api import ClientsInterestsRequest, MethodRequest, OnlineScoreRequest
import hashlib
from datetime import datetime

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
    print interests.invalid_fields
    assert interests.valid

#############################
######### Test API ##########
#############################


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
    def get(self, data):
        return self._store.get(key, None)


class TestApi(object):
    def __init__(self):
        self.context = {}
        self.headers = {}
        #self.store = MockKVStore()
    def get_response(self, request, store=None):
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
def test_score_request_ok(monkeypatchm arguments, test_api):
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": arguments, "method": u"online_score"}

        
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    assert code == api.OK



