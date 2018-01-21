def retry(exc=Exception, tries=3):
    def wrapper(f):
        def wrapped(*args, **kwargs):
            _tries = tries
            while True:
                try:
                    return f(*args, **kwargs)
                except exc:
                    _tries -= 1
                    if _tries <= 0:
                        raise
        return wrapped
    return wrapper


def retry_call(f, exc=Exception, args=None, kwargs=None, tries=3):
    _tries = tries
    args = args or []
    kwargs = kwargs or {}
    while True:
        try:
            return f(*args, **kwargs)
        except exc:
            _tries -= 1
            if _tries <= 0:
                raise
