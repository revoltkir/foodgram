from rest_framework import serializers
from recipes.models import (Tag, Ingredient, RecipeIngredient,
                            Recipe, Favorite, ShoppingCart)


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Для отображения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe (только чтение)."""

    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set', many=True, read_only=True
    )
    author = serializers.StringRelatedField(read_only=True)
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
