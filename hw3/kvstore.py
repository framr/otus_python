#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
from datetime import timedelta, datetime
from collections import namedtuple


Record = namedtuple("Record", "value update_time ttl")


class ZMQKVClient(object):
    def __init__(self, addr="tcp://127.0.0.1:42420"):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(addr)

    def _get(self, key, cache=False):
        cmd = "get" if not cache else "get_cache"
        self._socket.send(pickle.dumps((cmd, key, None)))
        data = pickle.loads(self._socket.recv())
        return Record(data["value"], data.get("update_time", None), data.get("ttl", None))

    def _set(self, key, value, cache=False):
        cmd = "set" if not cache else "set_cache"
        rec = {"value": value}
        self._socket.send(pickle.dumps((cmd, key, rec)))
        return self._socket.recv() == b"ok"

    def get(self, key):
        rec = self._get(key, cache=False)
        return rec.value

    def cache_get(self, key, cache=True):
        rec = self._get(key)
        dt = (datetime.now() - rec.update_time).total_seconds()
        if dt > rec.ttl:
            return None
        else:
            return rec.value

    def set(self, key, value):
        self._set(key, value, cache)        
        return self._socket.recv() == b"ok"

    def cache_set(self, key, value, ttl=3600):
        return self.set()


class ZMQKVServer(object):
    def __init__(self, addr="tcp://127.0.0.1:42420"):
        self._kvstore = {}
        self._kvstore_cache = {}
        self._context = zmq.Context()
        self._socket = zmq.socket(zmq.REP)
        self._socket.bind(addr)
        #https://stackoverflow.com/questions/7538988/zeromq-how-to-prevent-infinite-wait

    def run(self):
        while True:
            try:
                command, key, data = pickle.loads(socket.recv())
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
    server = ZMQServer()
    server.run()
