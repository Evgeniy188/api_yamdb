import logging

from rest_framework import permissions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_admin


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        return request.user.is_admin


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Разрешаем доступ только для безопасных методов (чтение)
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin or request.user.is_moderator:
            return True
        # Разрешаем доступ автору отзыва или администратору
        return obj.author == request.user or request.user.is_staff
