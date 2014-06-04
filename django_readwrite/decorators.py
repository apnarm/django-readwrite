import functools

from django.db import transaction
from django.forms.util import ErrorList
from django.utils.functional import wraps

from django_readwrite import signals
from django_readwrite.readonly import read_only_mode, ReadOnlyError


def full_clean_if_not_read_only(full_clean):
    """Decorator for preventing form submissions while in read-only mode."""

    def wrapper(self):
        full_clean(self)
        if read_only_mode:
            if '__all__' not in self._errors:
                self._errors['__all__'] = ErrorList()
            self._errors.get('__all__').insert(0, ReadOnlyError.message)
            if hasattr(self, 'cleaned_data'):
                delattr(self, 'cleaned_data')

    return wrapper



def transaction_decorator(queue_method, *args, **kwargs):

    if 'key' in kwargs:
        key = kwargs['key']
        func = None
    else:
        key = None
        func = args[0]

    # todo - set this automatically instead, based on whether this transaction has altered any m2m
    mandate_transaction = kwargs.get('mandate_transaction', False)

    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if not transaction.is_managed():
                if mandate_transaction:
                    raise Exception('Unable to continue, transaction required. Need to wrap this call in a transaction. See @commit_on_success.')
                # Not currently within a transaction,
                # so run the function immediately.
                return func(*args, **kwargs)
            else:
                # Allow a callable key function that takes
                # the same arguments as the function itself.
                if callable(key):
                    unique_key = key(*args, **kwargs)
                else:
                    unique_key = key
                # Queue the function to be called after
                # the current transaction is committed.
                closure = lambda: func(*args, **kwargs)
                # Now actually queue it.
                queue_method(closure, key=unique_key)

        return wrapped_func

    if func:
        return decorator(func)
    else:
        return decorator


post_commit = functools.partial(
    transaction_decorator,
    signals.queue_post_commit,
)

pre_commit = functools.partial(
    transaction_decorator,
    signals.queue_pre_commit,
)


def wrap(before=None, after=None, condition=lambda *args, **kwargs: True):
    """
    A helper for creating decorators.

    Runs a "before" function before the decorated function, and an "after"
    function afterwards. The condition check is performed once before
    the decorated function.

    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            yes = condition(*args, **kwargs)
            if yes and before:
                before()
            result = func(*args, **kwargs)
            if yes and after:
                after()
            return result
        return wrapped
    return decorator


def wrap_before(before, condition=lambda *args, **kwargs: True):
    """
    A helper for creating decorators.

    Runs a "before" function before the decorated function. The condition
    check is performed before the decorated function is called.

    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if condition(*args, **kwargs):
                before()
            return func(*args, **kwargs)
        return wrapped
    return decorator


def wrap_after(after, condition=lambda *args, **kwargs: True):
    """
    A helper for creating decorators.

    Runs an "after" function after the decorated function. The condition
    check is performed after the decorated function is called.

    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            result = func(*args, **kwargs)
            if condition(*args, **kwargs):
                after()
            return result
        return wrapped
    return decorator


managed = wrap(
    before=signals.send_pre_commit,
    after=signals.send_post_commit,
    condition=lambda flag=True, using=None: not flag and transaction.is_dirty(using=using),
)

commit_unless_managed = wrap(
    before=signals.send_pre_commit,
    after=signals.send_post_commit,
    condition=lambda using=None: not transaction.is_managed(using=using),
)

rollback_unless_managed = wrap_after(
    after=signals.send_post_rollback,
    condition=lambda using=None: not transaction.is_managed(using=using),
)

commit = wrap(
    before=signals.send_pre_commit,
    after=signals.send_post_commit,
)

rollback = wrap_after(
    after=signals.send_post_rollback,
)
