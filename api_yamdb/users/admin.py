from django.contrib import admin

from .models import CinemaUser


@admin.register(CinemaUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email")
