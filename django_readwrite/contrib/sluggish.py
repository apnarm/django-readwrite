# From https://gist.github.com/raymondbutcher/5262743

import time


class SluggishCache(object):
    """
    A partial wrapper for a Django cache API object. It will remember cache
    values in local memory for the specified delay time (in seconds) to
    avoid accessing the cache backend. This might be useful for a small
    number of keys which get accessed very frequently.

    It also supports dictionary-like access for getting, setting and deleting
    values.

    Be careful about storing too many keys with this, as they will take up
    memory in the Python application using it, plus in the cache backend.
    Also note that the values will only be eventually-correct; this wrapper
    trades accuracy for performance. In line with this, there is no thread
    safety surrounding these values. Don't use this for fast-changing values.
    Instead, use it for manually setting modes.

    Here is a rough comparison between some Django cache backends and
    SluggishCache. The memcache connection is to a single node running on
    localhost; in a clustered environment the difference is even greater.

        %timeit memcache.get('hello')
        10000 loops, best of 3: 124 us per loop

        %timeit locmem.get('hello')
        10000 loops, best of 3: 26.6 us per loop

        %timeit locmem_sluggish.get('hello')
        1000000 loops, best of 3: 1.5 us per loop

    But when SluggishCache gets a miss and has to check the cache backend,
    it will take as long as the wrapped cache object would plus some overhead.

        %timeit locmem_sluggish.get('hello')  # altered to always miss
        10000 loops, best of 3: 38.8 us per loop

    """

    missed = object()

    _values = {}

    def __init__(self, cache, delay=15):
        self.cache = cache
        self.delay = delay

    def __getitem__(self, key):
        value = self._get(key)
        if value is not self.missed:
            return value
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def _get(self, key):
        now = time.time()
        try:
            value, expires = self._values[key]
            if now > expires:
                raise KeyError
            return value
        except KeyError:
            value = self.cache.get(key, self.missed)
            self._values[key] = (value, now + self.delay)
            return value

    def get(self, key, default=None):
        value = self._get(key)
        if value is self.missed:
            return default
        else:
            return value

    def get_or_miss(self, key, miss=False):
        """
        Returns the cached value, or the "missed" object if it was not found
        in the cache. Passing in True for the second argument will make it
        bypass the cache and always return the "missed" object.

        Example usage:

            def get_value(refresh_cache=False):
                key = 'some.key.123'
                value = cache.get_or_miss(key, refresh_cache)
                if value is cache.missed:
                    value = generate_new_value()
                    cache.set(key, value)
                return value

        """

        return miss and self.missed or self.get(key, self.missed)

    def set(self, key, value, timeout=None):
        now = time.time()
        self._values[key] = (value, now + self.delay)
        self.cache.set(key, value, timeout)

    def delete(self, key):
        self.cache.delete(key)
        try:
            del self._values[key]
        except KeyError:
            pass
