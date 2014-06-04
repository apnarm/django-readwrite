from django.contrib.flatpages.views import flatpage
from django.http import Http404
from django.utils import simplejson

from django_readwrite.readonly import ReadOnlyError


def read_only_error(request, status=503):

    request.read_only_error = True

    if request.is_ajax():
        content = simplejson.dumps({
            'error': ReadOnlyError.message
        })
        return HttpResponse(content, status=status, content_type='application/json')

    try:
        return flatpage(request, '/readonly/', status=status)
    except Http404:
        content = ReadOnlyError.message
        return HttpResponse(content, status=status, content_type='text/plain')
