import collections
import random
import re

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS


def _build_mappings():
    result = collections.defaultdict(list)
    for db_alias, options in settings.DATABASES.items():
        for http_method in options.get('HTTP_METHODS', []):
            result[http_method].append(db_alias)
    return result


def _build_paths():
    result = {}
    for db_alias, options in settings.DATABASES.items():
        paths = options.get('HTTP_PATHS')
        if paths:
            any_path = '|'.join(re.escape(path) for path in paths)
            regex = re.compile(r'^(%s)' % any_path)
            result[db_alias] = regex
    return result


def _get_read_only_databases():
    result = []
    for db_alias, options in settings.DATABASES.items():
        for read_only_option in ('READ_ONLY', 'READ_ONLY_WARNING'):
            if options.get(read_only_option):
                result.append(db_alias)
                break
    return result


# Determine the HTTP method to database alias mappings.
# It will be in the format {http_method1: [alias1, alias2]}
DATABASE_MAPPINGS = _build_mappings()


# Determine a single fallback database to use.
# This persists for the entire life of the process, so it can be relied upon.
FALLBACK_DATABASE = random.choice(DATABASE_MAPPINGS.get(None) or [DEFAULT_DB_ALIAS])


# Determine which paths should be excluded from each database.
# For example, the /admin/ URLs should not really be read-only.
DATABASE_PATHS = _build_paths()


# Determine which databases are for read-only purposes.
READ_ONLY_DATABASES = _get_read_only_databases()
READ_ONLY_DATABASES_SET = set(READ_ONLY_DATABASES)
