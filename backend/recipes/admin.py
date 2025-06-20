from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeIngredient

admin.site.empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для модели Tag (тег)."""
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'slug', 'color')
    prepopulated_fields = {"slug": ("name",)}
    fields = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели Ingredient (ингредиент)."""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    """
    Вспомогательный inline для отображения ингредиентов
    в рецепте в админке.
    """
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для модели Recipe (рецепт). """
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('favorites_count',)

    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorited_by.count()

    favorites_count.short_description = 'В избранном'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """
    Админка для промежуточной модели RecipeIngredient (ингредиент в рецепте).
    """
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
