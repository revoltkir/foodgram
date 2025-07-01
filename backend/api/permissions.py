from rest_framework import permissions


class IsSuperuserOrAdminOrAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение, позволяющее редактировать
    или удалять объект его автору, админу или модератору.
    """

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_moderator
                    or request.user.is_admin
                    or obj.author == request.user))
