#!/usr/bin/env python
"""
Examples of asyncchat http request handler and asyncore usage can be found here
https://docs.python.org/2/library/asynchat.html
https://pymotw.com/2/asyncore/
http://code.activestate.com/recipes/259148-simple-http-server-based-on-asyncoreasynchat/
"""
from argparse import ArgumentParser
import asyncore_epoll
import asyncchat
from multiprocessing import Process
import logging
from logging import info
import socket
import namedtuple


#class HTTPHandler(object):
#    pass

HTTPHeaders = namedtuple("HTTPHeader", "method uri protocol content_length")
HTTPRequest = namedtuple("HTTPRequest", "body headers")


def parse_headers(data):
    pass


class HTTPProtocolMixins(object):
    """
    Decouples some HTTP logic
    methods named after counterparts in Lib/BaseHTTPServer.py
    """
    def send_error(self, code, msg=None):
        # 
        pass
    def push_to_wire(self, data):
        raise NotImplementedError
    def do_GET(self):
        pass
    def do_HEAD(self):
        pass

    def do_method(self, meth):
        try:
            meth_func = getattr(self, "do_%s" % meth)
            meth_func()
        except AttributeError:
            self.send_error()            



class HTTPRequestHandler(asynchat.async_chat):
    # XXX: what about next request on the same socket???
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
        
    def do_GET(self):
        pass
    def do_HEAD(self):
        pass


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
