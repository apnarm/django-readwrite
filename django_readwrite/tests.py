from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.test import TestCase

from django_readwrite.readonly import read_only_mode, ReadOnlyError

from apncore.util.unittest import RollbackTestCase


class ReadOnlyTestCase(TestCase):

    def setUp(self):
        """
        Record the current state of read-only mode and then ensure that it
        is enabled.

        """

        self.read_only_was_disabled = not read_only_mode
        if not read_only_mode:
            read_only_mode.enable()

        self.assertTrue(read_only_mode)

    def tearDown(self):
        """Revert the read-only state."""
        if self.read_only_was_disabled:
            read_only_mode.disable()

    def test_save(self):
        try:
            ContentType.objects.all()[0].save()
            self.fail('ReadOnlyError was not raised, it should have been.')
        except ReadOnlyError:
            pass

    def test_modelform(self):

        # Create a bound form.
        ContentTypeForm = modelform_factory(ContentType)
        form = ContentTypeForm(data={})

        # It should have errors because it's empty, and be invalid.
        self.assertFalse(form.is_valid())

        # The read-only error message should have been added to the form.
        self.assertTrue(ReadOnlyError.message in form._errors.get('__all__', {}))
