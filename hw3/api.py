#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import logging
from logging import info, error, exception
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from model_v1 import CharField, ArgumentsField, EmailField, PhoneField, DateField, BirthDayField, GenderField,\
        ClientIDsField, ValidatedRequest, nonempty
from scoring import get_score, get_interests


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


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest.decode(encoding="utf-8") == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    """
    1 - create MethodRequest and validate request
    2 - check auth
    3 - create and validate Request class for specific request type
    """

    method_req = MethodRequest(request["body"], ctx, store)
    try:
        method_req.parse_request()
    except ValueError:
        exception("got error while parsing request")
        return method_req.validate_message, INVALID_REQUEST
    if not check_auth(method_req):
        exception("wrong request format")
        return ERRORS[FORBIDDEN], FORBIDDEN

    if method_req.method == u"online_score":
        info("online_score method called")
        handler = OnlineScoreRequest(method_req, ctx, store)
    elif method_req.method == u"clients_interests":
        handler = ClientsInterestsRequest(method_req, ctx, store)
        info("online_score method called")
    else:
        error("wrong method %s" % method_req.method)
        return "wrong method %s" % method_req.method, INVALID_REQUEST
    try:
        handler.parse_request()
        handler.process()
    except ValueError:
        exception("wrong request format")
        return handler.validate_message, INVALID_REQUEST

    res = json.dumps(handler.process())
    return res, OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

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
