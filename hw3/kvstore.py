#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
from collections import namedtuple
import pickle
import datetime

Record = namedtuple("Record", "value update_time ttl")


class ZMQKVClient(object):
    def __init__(self, addr="tcp://127.0.0.1:42420"):
        self._context = zmq.Context()
        self._addr = addr

    def init_connection(self):
        self._socket = self._context.socket(zmq.REQ)
        # https://stackoverflow.com/questions/7538988/zeromq-how-to-prevent-infinite-wait
        self._socket.RCVTIMEO = 30  # XXX: not tested
        self._socket.SNDTIMEO = 30  # XXX: not tested
        self._socket.connect(self._addr)
        return self

    def _get(self, key, cache=False):
        cmd = "get" if not cache else "get_cache"
        # should we reconnect on error? read zmq docs..
        self._socket.send(pickle.dumps((cmd, key, None)))
        data = pickle.loads(self._socket.recv()) or {}
        return Record(data.get("value", None), data.get("update_time", None), data.get("ttl", None))

    def _set(self, key, value, cache=False, ttl=None):
        cmd = "set" if not cache else "set_cache"
        rec = {"value": value, "update_time": datetime.now(), "ttl": ttl}
        self._socket.send(pickle.dumps((cmd, key, rec)))
        return self._socket.recv() == b"ok"

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
