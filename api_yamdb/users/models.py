from api.roles import RoleEnum
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def validate_username_me(value):
    if value.lower() == 'me':
        raise ValidationError(
            _('Username cannot be "me".'),
            params={'value': value},
        )


class CinemaUser(AbstractUser):
    @property
    def is_admin(self):
        return (self.role == RoleEnum.ADMIN
                or self.is_superuser or self.is_staff)

    @property
    def is_moderator(self):
        return self.role == RoleEnum.MODERATOR

    role = models.CharField(max_length=20, choices=RoleEnum.choices,
                            default=RoleEnum.USER)

    bio = models.TextField(blank=True, null=False, default='')

    email = models.EmailField(_('email address'),
                              max_length=254, blank=True, unique=True)

    confirmation_code = models.CharField(max_length=6,
                                         blank=True, null=False, default='')

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=_('Enter a valid username.'
                          'This value may contain only letters,'
                          'numbers, and @/./+/-/_ characters.')
            ),
            validate_username_me
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username
