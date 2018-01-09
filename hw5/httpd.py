#!/usr/bin/env python
"""
Examples of asyncchat http request handler and asyncore usage can be found here
https://docs.python.org/2/library/asynchat.html
https://pymotw.com/2/asyncore/
http://code.activestate.com/recipes/259148-simple-http-server-based-on-asyncoreasynchat/
"""
from argparse import ArgumentParser
import asyncore_epoll
import asynchat
from multiprocessing import Process
import logging
from logging import info
import socket
import namedtuple
import urllib
import mimetypes
import os


HTTPHeaders = namedtuple("HTTPHeader", "method uri protocol content_length")
HTTPRequest = namedtuple("HTTPRequest", "body headers")


def parse_headers(data):
    pass


def translate_path(self, path, workdir=None):
    """
    Translate PATH to the local filename syntax.
    """
    # abandon query parameters
    path = path.split('?',1)[0]
    path = path.split('#',1)[0]
    path = urllib.unquote(path)
    parts = path.split('/')
    workdir = workdir or "."
    return os.path.join(workdir, *parts)


def guess_content_type(path):
    try:
        ctype = mimetypes.types_map[os.path.splitext(path)[1].lower()]
    except KeyError:
        return "application/octet-stream"
    

class HTTPProtocolMixins(object):
    """
    Decouples some HTTP logic.
    Methods named after counterparts in Lib/BaseHTTPServer.py
    """
    def do_GET(self):
        fd = self.send_head()
        if fd:
            self.push_to_wire_with_producer(asynchat.simple_producer(fd.read()))
            fd.close()
        self.handle_close()

    def do_HEAD(self):
        fd = self.send_head()
        if fd:
            fd.close()
        self.handle_close()

    def send_head(self):
        """
        This sends the response code and MIME headers.
        Common method for do_GET, do_HEAD.
        """
        path = self.translate_path(self.request.headers.uri)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
    
        if not os.path.isfile(path):
            self.send_error(404)
            return None    
        try:
            fd = open(path, "rb")
        except Exception:
            self.send_error(500, "Error opening file")
            return None

        self.send_response(200)
        self.send_header("Content-type", guess_content_type(path))
        self.send_header("Content-Length", os.fstat(fd))
        self.end_headers
        return fd

    def send_error(self, code, msg=None):
        try:
            short_msg, long_msg = self.responses[code]
        except KeyError:
            short_msg, long_msg = "???", "???"
        if msg is None:
            msg = short_msg
        #explain = long_msg
        self.send_response(code, msg)
        self.send_header("Connection", "close")
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def send_response(self, code, message=None):
        """
        Send response header
        """
        message = message or ""
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %d %s\r\n" %
                             (self.protocol_version, code, message))
            # print (self.protocol_version, code, message)
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())


    def send_header(self, keyword, value):
        """
        Send single header keyword: value 
        """

    def end_headers(self):
        """
        Send the blank line ending the MIME headers.
        """

    def push_to_wire(self, data):
        raise NotImplementedError
    def push_to_wire_with_producer(self, data):
        raise NotImplementedError

    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this resource.'),
        500: ('Internal Server Error', 'Server got itself in trouble')
        }


class HTTPRequestHandler(asynchat.async_chat):
    def __init__(self, sock):
        asynchat.async_chat.__init__(self, sock=sock)
        self.ibuffer = []
        self.set_terminator("\r\n\r\n")
        self.reading_headers = True
        self.handling = False
        self.request = HTTPRequest()

    def collect_incoming_data(self, data):
        """
        mandatory method
        """
        self.ibuffer.append(data)

    @property
    def data(self):
        d = "".join(self.ibuffer)
        del self.ibuffer[:]
        return d

    def push_to_wire(self, data):
        self.push(data)

    def push_to_wire_with_producer(self, data):
        self.push_with_producer(data)

    def found_terminator(self):
        """
        callback activated on terminator, mandatory method
        """
        if self.reading_headers:
            self.request.headers = parse_headers(self.data)
            if not self.request.headers:
                self.send_error(400, "Error parsing headers")
                self.handle_close()

            self.ibuffer = []
            if header.method == "POST":
                # we have more data to read
                self.set_terminator(self.request.headers.content_length)
            else:
                self.set_terminator(None)
                self.handle_request()
        elif not self.handling:
            # browsers sometime oversend
            # https://docs.python.org/2/library/asynchat.html
            self.set_terminator(None)            
            self.handling = True
            self.request.body = self.data
            self.handle_request()

        # XXX: when we are done with current request, can next request come in the same client socket?
        # If it is possible, we have to reset the hander state

    def handle_request(self):
        mname = self.request.method
        meth_func = getattr(self, "do_%s" % mname, None)
        if not meth_func:
            self.send_error(501, "Unsupported method (%r)" % mname)
            self.handle_close()
            return
        meth_func()


class AsyncoreServer(asyncore_epoll.dispatcher):
    def __init__(self, work_dir=".", host="127.0.0.1", port="8889", lsock_backlog=128):
        asyncore_epoll.dispatcher.__init__(self)
        # create listening socket and push it into epoll/select map
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # https://www.nginx.com/blog/socket-sharding-nginx-release-1-9-1/ 
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.bind((host, port))
        self.listen(lsock_backlog)

    def handle_accept(self):
        client_info = self.accept()
        if client_info: 
            sock, addr = client_info
            HTTPRequestHandler(sock)

    def serve_forever(self):
        try:
            asyncore_epoll.loop(timeout=2, poller=asyncore_epoll.epoll_poller)
        except Exception:
            pass
        except BaseException:
            info("server shutdown")
        finally:
            self.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", dest="workers", type=int, default=1, help="Number of workers")
    parser.add_argument("-r", dest="document_root", type=str, default=".", help="Web server internal storage path")
    parser.add_argument("-h", "--host", dest="host", type=str, default="127.0.0.1", help="host")
    parser.add_argument("-p", "--port", dest="port", type=int, default=8889, help="port")
    args = parser.parse_args()

    pool = []
    for _ in range(args.workers):
        server = AsyncoreServer(work_dir=args.document_root, host=args.host, port=args.port)
        p = Process(target=server.serve_forever)
        p.start()
        pool.append(p)

    info("All my workers are dead")
    for p in pool:
        p.join()
