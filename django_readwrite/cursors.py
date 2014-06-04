import logging
import re
import sys
import time

from django.db import connections
from django.utils.encoding import smart_unicode, force_unicode, smart_str

from django_readwrite.readonly import read_only_mode, ReadOnlyError


class RestrictedDatabaseError(Exception):
    def __init__(self, alias, sql):
        message = 'Trying to use database %r for the query: %s' % (alias, sql)
        super(RestrictedDatabaseError, self).__init__(smart_str(message))


class RestrictedCursorWrapper(object):

    READ_SQL_RE = re.compile(r'\s*(SELECT|EXPLAIN|SAVEPOINT|RELEASE SAVEPOINT|ROLLBACK TO SAVEPOINT)\b', re.IGNORECASE)

    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db  # Instance of a BaseDatabaseWrapper subclass

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def execute(self, sql, params=()):

        read_sql = bool(self.READ_SQL_RE.match(sql))

        db_options = connections.databases[self.db.alias]
        read_only_warning = db_options.get('READ_ONLY_WARNING')
        read_only_database = db_options.get('READ_ONLY') or read_only_warning

        if read_only_database:
            if not read_sql:
                if read_only_mode:
                    raise ReadOnlyError
                try:
                    raise RestrictedDatabaseError(self.db.alias, get_sql_output(sql, params))
                except RestrictedDatabaseError as error:
                    if not read_only_warning:
                        raise
                    logging.warning(
                        'RestrictedDatabaseWarning: %s' % smart_unicode(error)
                    )
        elif not read_sql and read_only_mode:
            raise ReadOnlyError

        return self.cursor.execute(sql, params)


class PrintCursorWrapper(RestrictedCursorWrapper):

    def execute(self, sql, params=()):
        try:
            try:
                start = time.time()
                result = super(PrintCursorWrapper, self).execute(sql, params)
            except Exception:
                sql = get_sql_output(sql, params)
                color = 'red'
                raise
            else:
                sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                options = connections.databases[self.db.alias]
                read_only = options.get('READ_ONLY') or options.get('READ_ONLY_WARNING')
                color = read_only and 'green' or 'purple'
                return result
        finally:
            elapsed = (time.time() - start) * 1000
            if elapsed < 1:
                time_taken = '%.4f ms' % elapsed
            else:
                time_taken = '%d ms' % elapsed
            sys.stderr.write('[%s] %s\n' % (time_taken, colorize(sql, color)))


def get_sql_output(sql, params):
    """Turns an sql string and params into something readable."""

    # Convert params to contain Unicode values.
    to_unicode = lambda s: force_unicode(s, strings_only=True, errors='replace')
    if isinstance(params, (list, tuple)):
        u_params = tuple([to_unicode(val) for val in params])
    else:
        u_params = dict([(to_unicode(k), to_unicode(v)) for k, v in params.items()])

    return smart_unicode(sql) % u_params


def colorize(message, color):
    terminal_colors = {
        'blue': '\033[94m',
        'green': '\033[92m',
        'purple': '\033[95m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'end': '\033[0m',
    }
    return terminal_colors[color] + message + terminal_colors['end']
