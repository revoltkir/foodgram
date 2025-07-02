from collections import defaultdict

from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Recipe, Ingredient, Favorite, ShoppingCart, \
    RecipeIngredient
from .filters import RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsSuperuserOrAdminOrAuthorOrReadOnly
from .serializers import RecipeSerializer, IngredientSerializer, \
    RecipeCreateSerializer, FavoriteSerializer, ShoppingCartSerializer, \
    RecipeShortSerializer
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from api.utils.shopping_cart import download_shopping_cart_response


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
        'favorite_set',
        'shoppingcart_set'
    )
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    ordering_fields = ('pub_date',)
    ordering = ('pub_date',)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateSerializer
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ('update', 'partial_update', 'destroy',
                           'download_shopping_cart'):
            return [IsSuperuserOrAdminOrAuthorOrReadOnly()]
        if self.action in ('favorite', 'shopping_cart'):
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_item(self, model, serializer_class, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'message': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model.objects.create(user=user, recipe=recipe)
        serializer = serializer_class(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_item(self, model, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        item = model.objects.filter(user=user, recipe=recipe)
        if not item.exists():
            return Response(
                {'message': 'Рецепт не найден в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        return self.add_item(Favorite, RecipeShortSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.remove_item(Favorite, request, pk)

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk=None):
        return self.add_item(ShoppingCart, RecipeShortSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.remove_item(ShoppingCart, request, pk)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Требуется авторизация.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        response = download_shopping_cart_response(request.user)
        if not response:
            return Response({'detail': 'Корзина пуста.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_fields = ('name',)
