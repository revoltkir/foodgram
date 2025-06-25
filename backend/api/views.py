from django.shortcuts import render
from rest_framework import viewsets
from recipes.models import Recipe
from .serializers import RecipeSerializer 


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения списка рецептов и одного рецепта."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
