import socket

from django.core.cache import cache as cache_backend

from django_readwrite.contrib.sluggish import SluggishCache


class ReadOnlyError(Exception):
    message = (
        'Sorry, your action cannot be processed because we are '
        'performing website maintenance. Please try again later.'
    )


class ReadOnlyManager(object):

    cache = SluggishCache(cache_backend, delay=5)
    cache_key = 'readwrite.readonly:%s' % socket.gethostname()

    def __nonzero__(self):
        return bool(self.cache.get(self.cache_key))

    def enable(self):
        two_weeks = 60 * 60 * 24 * 14
        self.cache.set(self.cache_key, True, two_weeks)

    def disable(self):
        self.cache.delete(self.cache_key)


read_only_mode = ReadOnlyManager()
