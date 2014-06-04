import contextlib
import threading

from django.db import connections

from django_readwrite.settings import FALLBACK_DATABASE


class ConnectionState(threading.local):

    _alias = FALLBACK_DATABASE

    def _get_alias(self):
        return self._alias

    def _set_alias(self, value):
        self._alias = value

    def _del_alias(self):
        self._alias = FALLBACK_DATABASE

    alias = property(_get_alias, _set_alias, _del_alias)

    @contextlib.contextmanager
    def force(self, value):
        old_value = self.alias
        self.alias = value
        try:
            yield
        finally:
            self.alias = old_value


class ConnectionProxy(object):

    def __init__(self, *args, **kwargs):
        with connection_state.force(None):
            super(ConnectionProxy, self).__init__(*args, **kwargs)

    def __getattribute__(self, name):
        alias = connection_state.alias
        connection = alias and connections[alias] or self
        return super(ConnectionProxy, connection).__getattribute__(name)

    def __setattr__(self, name, value):
        alias = connection_state.alias
        connection = alias and connections[alias] or self
        return super(ConnectionProxy, connection).__setattr__(name, value)


connection_state = ConnectionState()
