import base64
from django.core.files.base import ContentFile
from rest_framework import serializers


class SmartImageField(serializers.ImageField):
    """Обрабатывает как файл, так и base64-изображения."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                decoded_file = base64.b64decode(imgstr)
                file_name = f'temp_avatar.{ext}'
                data = ContentFile(decoded_file, name=file_name)
            except Exception:
                raise serializers.ValidationError(
                    'Ошибка при декодировании изображения в base64.')

        return super().to_internal_value(data)
