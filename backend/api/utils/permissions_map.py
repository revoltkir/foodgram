from rest_framework.permissions import AllowAny, IsAuthenticated
from api.permissions import IsSuperuserOrAdminOrAuthorOrReadOnly

user_permissions = {
    'me': [IsAuthenticated],
    'set_password': [IsAuthenticated],
    'subscribe': [IsAuthenticated],
    'subscriptions': [IsAuthenticated],
    'set_avatar': [IsAuthenticated],
    'delete_avatar': [IsAuthenticated],
}

recipe_permissions = {
    'create': [IsAuthenticated],
    'update': [IsSuperuserOrAdminOrAuthorOrReadOnly],
    'partial_update': [IsSuperuserOrAdminOrAuthorOrReadOnly],
    'destroy': [IsSuperuserOrAdminOrAuthorOrReadOnly],
    'download_shopping_cart': [IsAuthenticated],
    'favorite': [IsAuthenticated],
    'delete_favorite': [IsAuthenticated],
    'shopping_cart': [IsAuthenticated],
    'delete_shopping_cart': [IsAuthenticated],
    'get_shopping_cart': [IsAuthenticated],
}