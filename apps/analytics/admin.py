from django.contrib import admin

from .models import PageView


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("page_type", "page_slug", "city", "locality", "clinic", "created_at")
    list_filter = ("page_type", "city", "created_at")
    search_fields = ("page_slug", "path")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
