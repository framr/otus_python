#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import datetime
import logging
from logging import error, exception
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from model_v1 import CharField, ArgumentsField, EmailField, PhoneField, DateField, BirthDayField, GenderField,\
        ClientIDsField, ValidatedRequest
from scoring import get_score, get_interests
from kvstore import ZMQKVClient
from myretry import retry


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class MethodRequest(ValidatedRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def __init__(self, request, context, store):
        super(MethodRequest, self).__init__()
        self._request = request
        self._context = context

    @property
    def data(self):
        return self._request


class ClientsInterestsRequest(ValidatedRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def __init__(self, method_req, context, store):
        super(ClientsInterestsRequest, self).__init__()
        self._method_req = method_req
        self._store = store
        self._context = context

    @property
    def data(self):
        return self._method_req.arguments or {}

    def process(self):
        self._context.update({"nclients": len(self.client_ids)})
        res = {}
        for cid in self.client_ids:
            res[str(cid)] = get_interests(self._store, cid)
        return res


class OnlineScoreRequest(ValidatedRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, method_req, context, store):
        super(OnlineScoreRequest, self).__init__()
        self._method_req = method_req
        self._store = store
        self._context = context

    @property
    def data(self):
        return self._method_req.arguments or {}

    def parse_request(self):
        super(OnlineScoreRequest, self).parse_request()
        valid = any(["phone" in self.set_fields and "email" in self.set_fields,
                     "first_name" in self.set_fields and "last_name" in self.set_fields,
                     "gender" in self.set_fields and "birthday" in self.set_fields])
        if not valid:
            self.invalid_fields["combo"] = ("at least one of pairs (phone, email), (first name, last name), "
                                            "(gender, birhday) should be set")

    def process(self):
        self._context.update({"has": self.set_fields})
        if self._method_req.is_admin:
            return {"score": 42}
        score = get_score(self._store, self.phone, self.email, birthday=self.birthday, gender=self.gender,
                          first_name=self.first_name, last_name=self.last_name)
        return {"score": score}


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest.decode(encoding="utf-8") == request.token:
        return True
    return False


METHOD_ROUTING = {
        u"online_score": OnlineScoreRequest,
        u"clients_interests": ClientsInterestsRequest
    }


def method_handler(request, ctx, store):
    method_req = MethodRequest(request["body"], ctx, store)
    method_req.parse_request()
    if not method_req.valid:
        return method_req.validate_message, INVALID_REQUEST
    if not check_auth(method_req):
        exception("wrong request format")
        return ERRORS[FORBIDDEN], FORBIDDEN

    if method_req.method not in METHOD_ROUTING:
        error("wrong method %s" % method_req.method)
        return "wrong method %s" % method_req.method, INVALID_REQUEST
    handler = METHOD_ROUTING[method_req.method](method_req, ctx, store)
    handler.parse_request()
    if not handler.valid:
        return handler.validate_message, INVALID_REQUEST
    res = json.dumps(handler.process())
    return res, OK


# XXX: we should better catch only kvstore/network errors here
@retry(Exception, tries=3)
def get_store():
    try:
        conn = ZMQKVClient().init_connection()
    except Exception:
        exception("Error connecting to DB")
        conn = None
    return conn


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = get_store()

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            exception("Bad Request")
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
