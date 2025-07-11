from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import FoodgramUser

from .constants import (COOKING_TIME_MIN, INGREDIENT_AMOUNT_MAX,
                        INGREDIENT_AMOUNT_MIN, INGREDIENT_NAME_MAX_LENGTH,
                        MEASUREMENT_UNIT_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
                        TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH)


class Tag(models.Model):
    """Модель тега, используемого для рецептов."""
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название тега',
        help_text='Введите уникальное название тега.'
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
        verbose_name='Название ингредиента',
        help_text='Введите название ингредиента.'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
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
        FoodgramUser,
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
        blank=True, null=True,
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
        verbose_name='Теги рецепта',
        help_text='Выберите теги для рецепта.'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            COOKING_TIME_MIN,
            f'Время не может быть меньше {COOKING_TIME_MIN} мин.')
        ],
        verbose_name='Время приготовления (в минутах)',
        help_text='Укажите время приготовления в минутах'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def get_absolute_url(self):
        return f'/recipes/{self.pk}/'

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
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MIN,
                f'Минимальное количество — {INGREDIENT_AMOUNT_MIN}.'
            ),
            MaxValueValidator(
                INGREDIENT_AMOUNT_MAX,
                f'Максимальное количество — {INGREDIENT_AMOUNT_MAX}.'
            )
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


class Favorite(models.Model):
    """Модель избранных рецептов пользователей."""
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """Модель рецептов в корзине покупок пользователя."""
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart_recipe'
            )
        ]

    def __str__(self):
        return f'{self.recipe} в корзине у {self.user}'
