from collections import defaultdict

from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Recipe, Ingredient, Favorite, ShoppingCart
from .filters import RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsSuperuserOrAdminOrAuthorOrReadOnly
from .serializers import RecipeSerializer, IngredientSerializer, \
    RecipeCreateSerializer, FavoriteSerializer, ShoppingCartSerializer
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import AllowAny


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения списка рецептов и одного рецепта."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsSuperuserOrAdminOrAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Рецепт не в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if cart.exists():
                cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'Рецепта нет в корзине.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        ingredients_summary = defaultdict(lambda: {'amount': 0, 'unit': ''})

        for item in shopping_cart:
            recipe = item.recipe
            for ri in recipe.recipe_ingredients.all():  # related_name
                name = ri.ingredient.name
                unit = ri.ingredient.measurement_unit
                ingredients_summary[name]['amount'] += ri.amount
                ingredients_summary[name]['unit'] = unit

        lines = ['Список покупок:\n']
        for name, data in ingredients_summary.items():
            lines.append(f'{name}: {data["amount"]} {data["unit"]}')

        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_fields = ('name',)
