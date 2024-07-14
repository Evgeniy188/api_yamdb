from django.db import models
from django.contrib.auth.models import AbstractUser

from .roles import RoleEnum


class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=RoleEnum.choices(),
                            default=RoleEnum.USER)

    bio = models.TextField(blank=True, null=True)

    confirmation_code = models.CharField(max_length=6, blank=True, null=True)

    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username
