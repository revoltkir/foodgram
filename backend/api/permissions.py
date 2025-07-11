from rest_framework import permissions
from rest_framework.exceptions import MethodNotAllowed


class IsSuperuserOrAdminOrAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение, позволяющее редактировать
    или удалять объект его автору, админу или модератору.
    """

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or request.user.is_staff
            or obj.author == request.user
        )


class ReadOnly(permissions.BasePermission):
    """
    Разрешает только SAFE_METHODS, иначе 405 Method Not Allowed.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        raise MethodNotAllowed(request.method)
