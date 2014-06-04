import contextlib
import itertools
import threading

from Queue import Queue, Empty

from django.db import connections

from django_readwrite.connection import connection_state


class TemporaryConnectionPool(object):
    """
    An unlimited pool of temporary connections which can be used in
    isolation. An instance of this class should be created at the process
    level. Threads can safely "get" a connection using the get() context
    manager and have sole access to it for the duration of the context.

    """

    def __init__(self, alias_prefix, from_alias='default'):
        self.prefix = alias_prefix
        self.from_alias = from_alias
        self.count = itertools.count(1)
        self.lock = threading.Lock()
        self.connections = Queue()

    def _new_connection(self):
        """Create a new unique connection, using details from another."""
        with self.lock:
            alias = '%s%d' % (self.prefix, next(self.count))
            connections.databases[alias] = connections.databases[self.from_alias]
        return alias

    @contextlib.contextmanager
    def get(self):
        """
        Get or create a database connection for temporary use.
        The connection is automatically closed when the context exits.

        """
        try:
            alias = self.connections.get(block=False)
        except Empty:
            alias = self._new_connection()
        try:
            yield alias
        finally:
            with connection_state.force(None):
                connections[alias].close()
            self.connections.put(alias)
