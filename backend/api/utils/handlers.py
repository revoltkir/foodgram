from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, Http404) and response is not None:
        response.data = {'detail': 'Страница не найдена.'}
    return response
