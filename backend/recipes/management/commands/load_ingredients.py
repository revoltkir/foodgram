import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'Загружает ингредиенты из CSV файла (data/ingredients.csv)'

    def handle(self, *args, **kwargs):
        file_path = Path(settings.BASE_DIR) / 'data' / 'ingredients.csv'

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден.'))
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            new_ingredients = []
            existing = set(
                Ingredient.objects.values_list('name', 'measurement_unit')
            )

            for row in reader:
                if len(row) != 2:
                    self.stdout.write(
                        self.style.WARNING(f'Пропущена строка: {row}')
                    )
                    continue

                name, unit = row[0].strip(), row[1].strip()

                if (name, unit) not in existing:
                    new_ingredients.append(
                        Ingredient(name=name, measurement_unit=unit)
                    )
                    existing.add((name, unit))

        Ingredient.objects.bulk_create(new_ingredients)
        self.stdout.write(self.style.SUCCESS(
            f'Успешно загружено {len(new_ingredients)} ингредиентов.'
        ))
