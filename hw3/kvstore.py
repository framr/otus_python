#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
from collections import namedtuple
import pickle
import datetime

Record = namedtuple("Record", "value update_time ttl")


class ConnectionError(Exception):
    pass


class Connection(object):
    def __init__(self, addr="tcp://127.0.0.1:42420", timeout=60, retries=3):
        self._context = zmq.Context(1)
        self._addr = addr
        self._poller = zmq.Poller()
        self._retries = retries
        self._timeout = timeout

    def init_connection(self):
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(self._addr)
        return self

    def send(self, data, timeout=None):
        # implementes Lazy Pirate pattern
        # http://zguide.zeromq.org/page:all#Client-side-Reliability-Lazy-Pirate-Pattern
        _timeout = timeout or self._timeout
        retries_left = self._retries
        while retries_left > 0:
            self._poller.register(self._socket, zmq.POLLIN)
            self._socket.send(data)
            socks = dict(poll.poll(_timeout))
            if socks.get(self._socket) == zmq.POLLIN:
                reply = self._socket.recv()
                if reply:
                    return reply

            # error, reconnect
            self._socket.setsockopt(zmq.LINGER, 0)
            self._socket.close()
            self._poller.unregister(self._socket)
            retries_left -= 1
            # restore client socket
            self.init_connection()
            if retries_left <= 0:
                raise ConnectionError("Cannot send data to server")


class ZMQKVClient(object):
    def __init__(self, addr="tcp://127.0.0.1:42420", timeout=60, retries=3):
        self._conn = Connection()
    
    def init_connection(self):
        self._conn.init_connection()

    def _get(self, key, cache=False):
        cmd = "get" if not cache else "get_cache"
        # should we reconnect on error? read zmq docs..
        res = self._conn.send(pickle.dumps((cmd, key, None)))
        data = pickle.loads(res) or {}
        return Record(data.get("value", None), data.get("update_time", None), data.get("ttl", None))

    def _set(self, key, value, cache=False, ttl=None):
        cmd = "set" if not cache else "set_cache"
        rec = {"value": value, "update_time": datetime.now(), "ttl": ttl}
        res = self._conn.send(pickle.dumps((cmd, key, rec)))
        return res == b"ok"

    def get(self, key):
        rec = self._get(key, cache=False)
        return rec.value

    def cache_get(self, key):
        rec = self._get(key, cache=True)
        if rec.ttl:
            dt = (datetime.now() - rec.update_time).total_seconds()
            if dt > rec.ttl:
                return None
        return rec.value

    def set(self, key, value):
        return self._set(key, value, cache=False)

    def cache_set(self, key, value, ttl=3600):
        return self._set(key, value, cache=True)


class ZMQKVServer(object):
    def __init__(self, addr="tcp://127.0.0.1:42420"):
        self._kvstore = {}
        self._kvstore_cache = {}
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self._socket.bind(addr)

    def run(self):
        while True:
            try:
                command, key, data = pickle.loads(self._socket.recv())
                if command in ("set_cache", "get_cache"):
                    store = self._kvstore
                elif command in ("set", "get"):
                    store = self._kvstore_cache
                else:
                    raise ValueError
                if command.startswith("set"):
                    store[key] = data
                    self._socket.send(b"ok")
                else:
                    result = store.get(key, None)
                    self._socket.send(pickle.dumps(result))
            except Exception as e:
                print e


if __name__ == "__main__":
    server = ZMQKVServer()
    server.run()
