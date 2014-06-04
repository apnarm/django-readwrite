try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

from django.dispatch import Signal
from django.utils.datastructures import SortedDict


class FunctionPool(local):
    """
    A function pool that uses thread locals for storage. This is used to
    queue up functions to run once when necessary. This means that each
    thread has its own pool of messages.

    """

    def __iter__(self):
        """Return all queued functions."""
        if hasattr(self, '_thread_data'):
            for key, value in self._thread_data.iteritems():
                if key:
                    yield value
                else:
                    for item in value:
                        yield item

    def __len__(self):
        if hasattr(self, '_thread_data'):
            return len(self._thread_data)
        else:
            return 0

    def execute(self):
        """Execute all queued functions."""

        # Get all of the queued functions.
        functions = list(self)

        # Ensure the queue is cleared before running any functions.
        # This avoids triggering another post_commit signal, which would
        # execute this again, getting into an infinite loop.
        self.clear()

        # Run the functions.
        for func in functions:
            func()

    def queue(self, func, key=None):
        """
        Queues a function to call after the transaction is committed. Use a key
        when you want to ensure that an action won't get triggered multiple
        times.

        Eg. you might want queue this function (lambda: sync_account(123))
        multiple times, but it only makes sense to run it once after a
        transaction is committed. In this case, you could use the key
        'sync_account.123' to ensure it only runs ones.

        """

        if not hasattr(self, '_thread_data'):
            self._thread_data = SortedDict()

        if key:
            self._thread_data[key] = func
        else:
            self._thread_data.setdefault(None, [])
            self._thread_data[None].append(func)

    def clear(self):
        if hasattr(self, '_thread_data'):
            del self._thread_data


pre_commit = Signal()
post_commit = Signal()
post_rollback = Signal()

pre_commit_function_pool = FunctionPool()
post_commit_function_pool = FunctionPool()


def queue_pre_commit(func, key=None):
    """
    Queues a function to call before the transaction is committed. Use a
    key when you want to ensure that an action won't get triggered multiple
    times.

    Eg. you might want queue this function (lambda: validate_account(123))
    multiple times, but it only makes sense to run it once just before a
    transaction is committed. In this case, you could use the key
    'validate_account.123' to ensure it only runs once.

    """

    pre_commit_function_pool.queue(func, key=key)


def queue_post_commit(func, key=None):
    """
    Queues a function to call after the transaction is committed. Use a key
    when you want to ensure that an action won't get triggered multiple
    times.

    Eg. you might want queue this function (lambda: sync_account(123))
    multiple times, but it only makes sense to run it once after a
    transaction is committed. In this case, you could use the key
    'sync_account.123' to ensure it only runs once.

    """

    post_commit_function_pool.queue(func, key=key)


def send_pre_commit():
    pre_commit.send(sender=None)
    pre_commit_function_pool.execute()


def send_post_commit():
    post_commit.send(sender=None)
    post_commit_function_pool.execute()


def send_post_rollback():
    post_rollback.send(sender=None)
    pre_commit_function_pool.clear()
    post_commit_function_pool.clear()
