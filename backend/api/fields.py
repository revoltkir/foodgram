from rest_framework.fields import ImageField
from drf_extra_fields.fields import Base64ImageField
from django.core.files.uploadedfile import InMemoryUploadedFile


class SmartImageField(Base64ImageField):
    def to_internal_value(self, data):
        # Если это обычный файл — обрабатываем как ImageField
        if isinstance(data, InMemoryUploadedFile):
            return ImageField().to_internal_value(data)
        # Если это base64 — обрабатываем как Base64
        return super().to_internal_value(data)
