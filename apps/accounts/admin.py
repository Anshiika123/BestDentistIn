from django.contrib import admin

from .models import ClinicUser


@admin.register(ClinicUser)
class ClinicUserAdmin(admin.ModelAdmin):
    list_display = ("user", "clinic", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "clinic")
    search_fields = ("user__username", "user__email", "clinic__name")
