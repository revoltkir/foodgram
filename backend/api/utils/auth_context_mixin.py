class AuthContextMixin:
    """
    Миксин для получения авторизованного
    пользователя из контекста сериализатора.
    """

    def get_authenticated_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return user if user and user.is_authenticated else None
