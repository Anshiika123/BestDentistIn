from django.contrib import admin

from .models import City, Locality


class LocalityInline(admin.TabularInline):
    model = Locality
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "state", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [LocalityInline]


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "slug", "is_active")
    list_filter = ("city", "is_active")
    prepopulated_fields = {"slug": ("name",)}
