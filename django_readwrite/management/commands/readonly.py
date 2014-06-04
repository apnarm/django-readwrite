from django.core.management.base import BaseCommand, CommandError

from django_readwrite.readonly import read_only_mode


class Command(BaseCommand):

    help = 'Manage the read-only status of the database.'
    args = 'enable|disable|status'

    can_import_settings = False
    requires_model_validation = False

    def handle(self, action=None, **options):

        if not action:
            print self.usage()
            self.status()
            return

        methods = {
            'enable': self.enable,
            'disable': self.disable,
            'status': self.status,
        }
        try:
            method = methods[action]
        except KeyError:
            raise CommandError(self.usage('readonly'))
        else:
            method()

    def enable(self):
        read_only_mode.enable()
        self.status()

    def disable(self):
        read_only_mode.disable()
        self.status()

    def status(self):
        if read_only_mode:
            print 'Server is in read-only mode'
        else:
            print 'Server is in read/write mode'

    def usage(self, subcommand='readonly'):
        return 'Usage: %s [%s]' % (subcommand, self.args)
