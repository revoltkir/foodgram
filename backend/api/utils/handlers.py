from django.http import Http404
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для DRF.
    Возвращает специальное сообщение для 404 (Http404).
    """
    response = exception_handler(exc, context)
    if isinstance(exc, Http404) and response is not None:
        response.data = {'detail': 'Страница не найдена.'}
    return response
