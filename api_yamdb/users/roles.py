from enum import Enum


class RoleEnum(Enum):
    ANONYMOUS = 'anonymous'
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    SUPERUSER = 'superuser'

    @classmethod
    def choices(cls):
        return [(role.value, role.value) for role in cls]
