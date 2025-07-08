from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient, Tag


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов по тегам, автору, избранному и корзине.
    """
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label='В избранном'
    )

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='В корзине покупок'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги рецепта'
    )
    author = filters.NumberFilter(
        field_name='author__id',
        label='Автор рецепта (ID)'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shoppingcart__user=user)
        return queryset


class IngredientSearchFilter(filters.FilterSet):
    """Фильтр для поиска ингредиентов по началу имени."""
    name = filters.CharFilter(method='filter_name_startswith')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name_startswith(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)
