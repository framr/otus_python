#!/usr/bin/env python
import sys
import json
sys.path.append("../")

from kvstore import ZMQKVClient
from scoring import user_key


if __name__ == "__main__":
    client = ZMQKVClient()
    client.init_connection()
    client.set("i:1", json.dumps(("movies", "animals")))
    client.set("i:2", json.dumps(("ml", "python")))
    client.cache_set(user_key(first_name=u"Darth", last_name=u"Vader"), 100500)

