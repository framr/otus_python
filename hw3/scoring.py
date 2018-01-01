import hashlib
import json
from retry.api import retry_call
from logging import exception


def user_key(first_name=None, last_name=None, birthday=None):
    key_parts = [
        first_name or "",
        last_name or "",
        #birthday.strftime("%Y%m%d") if birthday else "",
        birthday or ""
    ]
    key = "uid:" + hashlib.md5("".join(key_parts)).hexdigest()
    return key


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    
    key = user_key(first_name=first_name, last_name=last_name, birthday=birthday)
    # try get from cache,
    # fallback to heavy calculation in case of cache miss 
    cached = None
    try:
        cached = store.cache_get(key)
        print cached
    except Exception:
        # XXX: hope rps is not very high (otherwise remove prints?)
        # should we store cache miss ratio?
        exception("cache error")
    score = cached or 0
    if score: # WTF: score = 0.0 is not allowed?
        return score

    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    try:
        store.cache_set(key, score,  60 * 60)
    except Exception:
        # XXX: hope rps is not very high (otherwise remove prints?)
        # should we store cache miss ratio?
        exception("cache set error")
    return score


def get_interests(store, cid):
    r = retry_call(store.get, ["i:%s" % cid])
    return json.loads(r) if r else []
