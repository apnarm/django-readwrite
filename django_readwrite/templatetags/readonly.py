from django import template

from django_readwrite.readonly import read_only_mode


register = template.Library()


class ReadOnlyNode(template.Node):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        if read_only_mode:
            return self.nodelist.render(context)
        else:
            return ''


@register.tag
def if_read_only(parser, token):
    nodelist = parser.parse(('endif_read_only',))
    parser.delete_first_token()
    return ReadOnlyNode(nodelist)
