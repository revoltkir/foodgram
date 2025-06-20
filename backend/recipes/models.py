from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.contrib.auth import get_user_model

from constants import *

User = get_user_model()


class Tag(models.Model):
    """Модель тега, используемого для рецептов."""
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название тега',
        help_text='Введите уникальное название тега.'
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цвет (HEX)',
        help_text='HEX-код цвета, например #49B64E',
        validators=[RegexValidator(
            regex=r'^#([A-Fa-f0-9]{6})$',
            message='Введите цвет в формате HEX, например #49B64E.'
        )]
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Идентификатор тега',
        help_text='Допустимы только латиница, цифры, дефис и подчёркивание.',
        validators=[RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$',
            message='Идентификатор тега содержит недопустимый символ.'
        )]
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента для рецептов."""
    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название ингредиента',
        help_text='Введите название ингредиента.'
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
        help_text='Например: граммы, мл, штуки.'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта, публикуемого пользователями."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта.'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение рецепта',
        help_text='Загрузите изображение блюда.'
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Опишите способ приготовления.'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты и их количество.'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        help_text='Выберите теги для рецепта.'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            COOKING_TIME_MIN,
            f'Время не может быть меньше {COOKING_TIME_MIN} мин.')
        ],
        verbose_name='Время приготовления (в минутах)'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи ингредиента с рецептом."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            INGREDIENT_AMOUNT_MIN,
            f'Минимальное количество — {INGREDIENT_AMOUNT_MIN}.')
        ],
        verbose_name='Количество',
        help_text='Укажите количество ингредиента.'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name} — {self.amount}'
