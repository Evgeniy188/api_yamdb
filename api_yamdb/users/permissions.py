from rest_framework import permissions

from .roles import RoleEnum

from django.contrib.auth.models import AnonymousUser

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class IsSuperUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (request.user.role == RoleEnum.ADMIN.value
                or request.user.is_superuser)


class IsModerator(permissions.BasePermission):

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (request.user.role in [RoleEnum.MODERATOR.value,
                                      RoleEnum.ADMIN.value]
                or request.user.is_superuser)


class IsUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return request.user.role in [RoleEnum.ADMIN.value,
                                     RoleEnum.MODERATOR.value,
                                     RoleEnum.USER.value,
                                     RoleEnum.SUPERUSER.value]


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if isinstance(request.user, AnonymousUser):
            return False
        return (request.user.role == RoleEnum.ADMIN.value
                or request.user.is_superuser)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Разрешаем доступ только для безопасных методов (чтение)
        if request.method in permissions.SAFE_METHODS:
            return True
        if isinstance(request.user, AnonymousUser):
            return False
        if (request.user.role in [RoleEnum.MODERATOR.value,
                                  RoleEnum.ADMIN.value]
                or request.user.is_superuser):
            return True
        # Разрешаем доступ автору отзыва или администратору
        return obj.author == request.user or request.user.is_staff
