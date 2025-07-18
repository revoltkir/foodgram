from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

MAX_LENGTH_EMAIL = 254
MAX_LENGTH_USERNAME = 150


class FoodgramUser(AbstractUser):
    """
    Кастомная модель пользователя для Foodgram.
    Авторизация по email, поддержка аватара.
    """

    email = models.EmailField(
        'email-адрес',
        max_length=MAX_LENGTH_EMAIL,
        unique=True
    )
    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=(
            [RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Юзернейм неверный!'
            )]
        )
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self) -> str:
        return f'{self.username}: {self.email}'


class Subscription(models.Model):
    """Модель подписки пользователя на автора."""
    user = models.ForeignKey(
        FoodgramUser,
        related_name='subscriber',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        FoodgramUser,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    date_added = models.DateTimeField(
        verbose_name='Дата создания подписки',
        auto_now_add=True,
        editable=False
    )

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на себя')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_author_user'
            ),
        )

    def __str__(self) -> str:
        return f'{self.user.username} подписан на: {self.author.username}'
