from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeIngredient, Favorite, \
    ShoppingCart
from django.utils.html import format_html

admin.site.empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Админка для модели Tag (тег).
    Отображает имя, цвет (цветной квадратик) и slug, позволяет искать
    и редактировать теги.
    """
    list_display = ('id', 'name', 'color_display', 'slug')
    search_fields = ('name', 'slug', 'color')
    prepopulated_fields = {"slug": ("name",)}
    fields = ('name', 'color', 'slug')

    @admin.display(description='Цвет')
    def color_display(self, obj):
        return format_html(
            '<div style="display:inline-block; width:20px; height:20px; '
            'background:{}; border:1px solid #000; margin-right:5px; vertical-align:middle"></div>{}',
            obj.color, obj.color
        )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели Ingredient (ингредиент)."""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    """
    Вспомогательный inline для отображения ингредиентов в рецепте в админке.
    """
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для модели Recipe (рецепт)."""
    list_display = ('id', 'name', 'author', 'favorites_count', 'image_display')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author', 'pub_date')
    inlines = [RecipeIngredientInline]
    readonly_fields = ('image_display', 'favorites_count')

    fields = (
        'name', 'author', 'image', 'image_display', 'text',
        'cooking_time', 'favorites_count', 'tags'
    )

    @admin.display(description='Фото')
    def image_display(self, obj):
        """Показывает превью изображения рецепта в админке."""
        if obj.image and hasattr(obj.image, 'url'):
            return format_html("<img src='{}' width='100' />", obj.image.url)
        return 'нет фото'

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_set.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """
    Админка для промежуточной модели RecipeIngredient (ингредиент в рецепте).
    """
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Админка для модели Favorite (избранное).
    """
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Админка для модели ShoppingCart (список покупок).
    """
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
