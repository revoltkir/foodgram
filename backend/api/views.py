from rest_framework import viewsets
from recipes.models import Recipe, Ingredient
from .serializers import RecipeSerializer, IngredientSerializer

from rest_framework.permissions import AllowAny


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения списка рецептов и одного рецепта."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_fields = ('name',)
