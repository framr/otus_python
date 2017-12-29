#!/usr/bin/env python
import pytest
import api
import hashlib
from datetime import datetime

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"


class TestApi(object):
    def __init__(self):
        self.context = {}
        self.headers = {}
        self.store = None
    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)
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
    {"first_name": 0, "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birhday": u"01.01.2018" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birhday": u"01.01.2018" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvaderyahoo.com", "birhday": u"01.01.2018" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birhday": u"2018.01.01" , "gender": 0},
    {"first_name": u"Darth", "last_name": u"Vader", "email": u"iamvader@yahoo.com", "birhday": u"2018.01.01" , "gender": 1}
    ])
def test_invalid_score_request(arguments, test_api):
    request = {"account": u"horns&hoofs", "login": u"h&f", "arguments": arguments, "method": u"online_score"}
    test_api.enforce_valid_token(request)
    msg, code = test_api.get_response(request)
    #print msg
    #assert True == False
    assert code == api.INVALID_REQUEST





