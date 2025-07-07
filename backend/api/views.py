from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Recipe, Ingredient, Favorite, ShoppingCart, Tag
from users.models import FoodgramUser, Subscription
from .filters import RecipeFilter, IngredientSearchFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsSuperuserOrAdminOrAuthorOrReadOnly, ReadOnly
from .serializers import RecipeSerializer, IngredientSerializer, \
    RecipeCreateSerializer, RecipeShortSerializer, TagSerializer, \
    UserSubscriptionSerializer, SubscriptionSerializer, \
    CreateUserSerializer, UserInfoSerializer, SetPasswordSerializer, \
    SetUserAvatarSerializer, RecipeLinkSerializer

from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters, status

from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from api.utils.shopping_cart import download_shopping_cart_response
from .utils.permissions_map import user_permissions, recipe_permissions


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUser | ReadOnly]
    pagination_class = None


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminUser | ReadOnly]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientSearchFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
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

    permission_classes = [AllowAny]
    permission_classes_by_action = recipe_permissions

    def get_permissions(self):
        perms = self.permission_classes_by_action.get(
            self.action, self.permission_classes
        )
        return [perm() for perm in perms]

    def get_serializer_class(self):
        if self.action in (
                'create', 'update', 'partial_update'
        ):
            return RecipeCreateSerializer
        if self.action in (
                'favorite', 'shopping_cart', 'delete_favorite',
                'delete_shopping_cart', 'get_shopping_cart'
        ):
            return RecipeShortSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_item(self, model, serializer_class, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response({'message': 'Рецепт уже добавлен'},
                            status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        serializer = serializer_class(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_item(self, model, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        item = model.objects.filter(user=request.user, recipe=recipe)
        if not item.exists():
            return Response({'message': 'Рецепт не найден в списке.'},
                            status=status.HTTP_400_BAD_REQUEST)
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
        return response  # <- response уже сам корректный

    @action(detail=False, methods=['get'], url_path='shopping_cart')
    def get_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(shoppingcart__user=user)
        serializer = RecipeShortSerializer(recipes, many=True,
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        serializer = RecipeLinkSerializer(recipe, context={
            'request': request})
        return Response(serializer.data)


class CustomUserViewSet(UserViewSet):
    """
    Кастомный вьюсет на базе Djoser для работы с пользователями:
    регистрация, профиль, подписки, смена пароля.
    """
    queryset = FoodgramUser.objects.all()
    pagination_class = LimitPageNumberPagination
    permission_classes = (AllowAny,)

    permission_classes_by_action = user_permissions

    def get_permissions(self):
        perms = self.permission_classes_by_action.get(
            self.action, self.permission_classes
        )
        return [perm() for perm in perms]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserInfoSerializer

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(FoodgramUser, pk=id)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'author': author.pk},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            response_serializer = UserSubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(response_serializer.data,
                            status=status.HTTP_201_CREATED)

        # DELETE: отписка
        subscription = Subscription.objects.filter(user=user,
                                                   author=author).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Вы не были подписаны на этого автора.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        authors = [sub.author for sub in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = UserSubscriptionSerializer(page, many=True, context={
            'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post', 'put', 'patch'],
            url_path='me/avatar')
    def set_avatar(self, request):
        if 'avatar' not in request.data or not request.data['avatar']:
            return Response({'avatar': 'Необходимо передать файл.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = SetUserAvatarSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
