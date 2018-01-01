import hashlib
import json
from retry.api import retry_call
from logging import exception


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        #birthday.strftime("%Y%m%d") if birthday else "",
        birthday or ""
    ]
    key = "uid:" + hashlib.md5("".join(key_parts)).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    
    try:
        cached = store.cache_get(key)
    except Exception:
        exception("cache error")

    score = cached or 0
    if score:
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
    retry_call(store.cache_set, [key, score,  60 * 60], tries=3)
    return score


def get_interests(store, cid):
    r = retry_call(store.get, ["i:%s" % cid])
    return json.loads(r) if r else []
