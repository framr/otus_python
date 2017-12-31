#!/usr/bin/env python
import pytest
import api


class TestApi(object):
    def __init__(self):
        self.context = {}
        self.headers = {}
        self.store = None
    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)


@pytest.fixture
def test_api():
    return TestApi()


@pytest.mark.parameterize("request", [{}])
def test__empty_request(request, test_api):
    _, code = test_api.get_response(request)
    assert code == api.INVALID_REQUEST
