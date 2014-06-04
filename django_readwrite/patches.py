from django.conf import settings
from django.db import connections, transaction
from django.db.backends import BaseDatabaseWrapper
from django.db.backends.dummy.base import DatabaseWrapper as DummyDatabaseWrapper
from django.forms.models import BaseModelForm

from django_readwrite import decorators
from django_readwrite.connection import ConnectionProxy
from django_readwrite.cursors import PrintCursorWrapper, RestrictedCursorWrapper


# Patch Django's transaction management functions to trigger signals.
transaction.managed = decorators.managed(transaction.managed)
transaction.commit_unless_managed = decorators.commit_unless_managed(transaction.commit_unless_managed)
transaction.rollback_unless_managed = decorators.rollback_unless_managed(transaction.rollback_unless_managed)
transaction.commit = decorators.commit(transaction.commit)
transaction.rollback = decorators.rollback(transaction.rollback)


# Patch Django's form class to handle read-only mode.
BaseModelForm.full_clean = decorators.full_clean_if_not_read_only(BaseModelForm.full_clean)


# Patch Django's connection classes (BaseDatabaseWrapper subclasses depending
# on which engines have been used in settings.DATABASES) to always use
# the "active" connection that is determined by the middleware.
for connection_class in set(conn.__class__ for conn in connections.all()):
    if connection_class is not DummyDatabaseWrapper:
        connection_class.__bases__ = (ConnectionProxy,) + connection_class.__bases__


# Patch Django's BaseDatabaseWrapper to enforce database write restrictions.
if settings.SQL_DEBUG and not settings.TEST_MODE:
    def cursor(self):
        cursor = self.make_debug_cursor(self._cursor())
        return PrintCursorWrapper(cursor, self)
elif settings.SQL_QUERY_DEBUG:
    def cursor(self):
        cursor = self.make_debug_cursor(self._cursor())
        return RestrictedCursorWrapper(cursor, self)
else:
    def cursor(self):
        return RestrictedCursorWrapper(self._cursor(), self)
BaseDatabaseWrapper.cursor = cursor
