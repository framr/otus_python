#!/usr/bin/env python
import sys
sys.path.append("../")
from kvstore import ZMQKVClient


if __name__ == "__main__":
    client = ZMQKVClient()
    client.set("a", 1)
    client.cache_set("b", 2)
    client.set(1, 2)

    print client.get("a")
    print client.get("b")
    print client.cache_get("b")
    print client.get(1)
