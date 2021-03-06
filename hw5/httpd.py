#!/usr/bin/env python
"""
Examples of asyncchat http request handler and asyncore usage can be found here
https://docs.python.org/2/library/asynchat.html
https://pymotw.com/2/asyncore/
http://code.activestate.com/recipes/259148-simple-http-server-based-on-asyncoreasynchat/
See also Lib/BaseHTTPServer.py and Lib/SimpleHTTPServer.py
"""
from argparse import ArgumentParser
import asyncore_epoll as asyncore
import asynchat
from multiprocessing import Process
import logging
from logging import info, exception
import socket
import urllib
import mimetypes
import os
import time
import cgi
import sys
from StringIO import StringIO


SUPPORTED_PROTOCOLS = ("HTTP/1.0", "HTTP/1.1")
RECREATE_INDEX_HTML = False

class ServerError(Exception):
    pass


def parse_headers(data, sep="\r\n"):
    splitted = data.split(sep)
    start_line, headers = splitted[0], splitted[1:]
    method, uri, protocol = start_line.split()
    if protocol not in SUPPORTED_PROTOCOLS:
        raise ServerError("protocol %s not supported" % protocol)
    result = {"Method": method, "URI": uri, "Protocol": protocol}
    for h in headers:
        if h:
            splitted = h.split(":", 1)
            result[splitted[0]] = splitted[1]
    return result


def url_basename(url):
    filename = url.split("/")[-1].split("#")[0].split("?")[0]
    base = "/".join(url.split("/")[:-1])
    return base, filename


def translate_path(path, workdir):
    """
    Translate path to the local filename syntax.
    """
    # abandon query parameters
    path = path.split('?', 1)[0]
    path = path.split('#', 1)[0]
    path = urllib.unquote(path)
    parts = path.split('/')
    return os.path.join(workdir, *parts)


def validate_root_escape(root, path):
    real = os.path.realpath(path)
    root_real = os.path.realpath(root)
    if real.startswith(root_real):
        return True
    return False


def guess_content_type(path):
    try:
        ctype = mimetypes.types_map[os.path.splitext(path)[1].lower()]
    except KeyError:
        return "application/octet-stream"
    return ctype


class SimpleFileProducer(object):
    def __init__(self, fd, buffer_size=512):
        self.fd = fd
        self.buffer_size = buffer_size

    def more(self):
        data = self.fd.read(self.buffer_size)
        if data:
            return data
        else:
            self.fd.close()
            return ""


class HTTPProtocolMixins(object):
    """
    Decouples some HTTP logic.
    Methods named after counterparts in Lib/BaseHTTPServer.py and Lib/SimpleHTTPServer.py
    """
    def do_GET(self):
        fd = self.send_head()
        if fd:
            self.push_to_wire_with_producer(SimpleFileProducer(fd))
            self.close_when_done()
        else:
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
        path = translate_path(self.headers["URI"], DOCUMENT_ROOT)
        if not validate_root_escape(DOCUMENT_ROOT, path):
            self.send_error(404)
            return None
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")

        if not os.path.isfile(path):
            fdir, fname = url_basename(path)
            if fname == "index.html":
                if RECREATE_INDEX_HTML:
                    index_html = self.list_directory(fdir)
                    return index_html
                else:
                    self.send_error(403)
            self.send_error(404)
            return None
        try:
            fd = open(path, "rb")
        except Exception:
            self.send_error(500, "Error opening file")
            return None

        self.send_response(200)
        self.send_header("Content-type", guess_content_type(path))
        self.send_header("Content-Length", str(os.fstat(fd.fileno())[6]))
        self.end_headers()
        return fd

    def list_directory(self, path):
        listing = os.listdir(path)
        listing.sort(key=lambda a: a.lower())
        f = StringIO()
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing</title>\n")
        f.write("<body>\n<h2>Directory listing</h2>\n")
        f.write("<hr>\n<ul>\n")
        for name in listing:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def send_error(self, code, msg=None):
        try:
            short_msg, long_msg = self.responses[code]
        except KeyError:
            short_msg, long_msg = "???", "???"
        if msg is None:
            msg = short_msg
        # explain = long_msg
        self.send_response(code, msg)
        self.send_header("Connection", "close")
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def send_response(self, code, message=None):
        """
        Send response header
        """
        if message is None:
            message = self.responses[code][0] if code in self.responses else ""
        self.push_to_wire("%s %s %s\r\n" % (self.headers["Protocol"], code, message))
        self.send_header("Server", "Blashyrkh")
        self.send_header("Date", self.date_time_string())

    def send_header(self, keyword, value):
        """
        Send single header keyword: value
        """
        self.push_to_wire("%s: %s\r\n" % (keyword, value))

    def end_headers(self):
        """
        Send the blank line ending the MIME headers.
        """
        self.push_to_wire("\r\n")

    def date_time_string(self):
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(time.time())
        return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
               self.weekdayname[wd], day, self.monthname[month], year, hh, mm, ss)

    def push_to_wire(self, data):
        raise NotImplementedError

    def push_to_wire_with_producer(self, data):
        raise NotImplementedError

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    responses = {
        100: ('Continue', 'Request received, please continue'),
        200: ('OK', 'Request fulfilled, document follows'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this resource.'),
        500: ('Internal Server Error', 'Server got itself in trouble')
        }


class HTTPRequestHandler(HTTPProtocolMixins, asynchat.async_chat):
    def __init__(self, sock):
        asynchat.async_chat.__init__(self, sock)
        self.ibuffer = []
        self.set_terminator("\r\n\r\n")
        self.reading_headers = True
        self.handling = False
        self.headers = None
        self.body = None

    def collect_incoming_data(self, data):
        """
        mandatory method
        """
        self.ibuffer.append(data)

    @property
    def data(self):
        d = "".join(self.ibuffer)
        #del self.ibuffer[:]
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
            self.reading_headers = False
            try:
                self.headers = parse_headers(self.data)
            except Exception:
                exception("error parsing headers")
                self.send_error(400, "Error parsing headers")
                self.handle_close()

            self.ibuffer = []
            if self.headers["Method"] == "POST":
                # we have more data to read
                l = self.headers.get("Content-Length", 0)
                if l == 0:
                    self.handle_request()
                else:
                    self.set_terminator(int(l))
            else:
                self.set_terminator(None)
                self.handle_request()
        elif not self.handling:
            # browsers sometime oversend
            # https://docs.python.org/2/library/asynchat.html
            self.set_terminator(None)
            self.handling = True
            self.body = self.data
            self.handle_request()

    def handle_request(self):
        mname = self.headers["Method"]
        meth_func = getattr(self, "do_%s" % mname, None)
        if not meth_func:
            self.send_error(405, "Unsupported method (%r)" % mname)
            self.handle_close()
            return
        meth_func()
        #self.handle_close()


class AsyncoreServer(asyncore.dispatcher):
    def __init__(self, work_dir=".", host="127.0.0.1", port="8889", lsock_backlog=128):
        asyncore.dispatcher.__init__(self)
        # create listening socket and push it into epoll/select map
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # https://www.nginx.com/blog/socket-sharding-nginx-release-1-9-1/
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.bind((host, port))
        self.listen(lsock_backlog)
        self.host = host
        self.port = port

    def handle_accept(self):
        client_info = self.accept()
        if client_info:
            #info("got client")
            sock, addr = client_info
            HTTPRequestHandler(sock)

    def serve_forever(self):
        try:
            info("Starting server at %s:%s" % (self.host, self.port))
            asyncore.loop(timeout=2, poller=asyncore.epoll_poller)
        except Exception:
            exception("Server got error")
        except BaseException:
            info("Server shutdown")
        finally:
            info("Server exit")
            self.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", dest="workers", type=int, default=1, help="Number of workers")
    parser.add_argument("-r", dest="document_root", type=str, default=".", help="Web server internal storage path")
    parser.add_argument("--host", dest="host", type=str, default="127.0.0.1", help="host")
    parser.add_argument("-p", "--port", dest="port", type=int, default=8889, help="port")
    parser.add_argument("--log", dest="log", type=str, default=None, help="log file")
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    DOCUMENT_ROOT = args.document_root

    pool = []
    for _ in range(args.workers):
        server = AsyncoreServer(work_dir=args.document_root, host=args.host, port=args.port)
        p = Process(target=server.serve_forever)
        p.start()
        pool.append(p)
    for p in pool:
        p.join()
    info("All my workers are dead")
