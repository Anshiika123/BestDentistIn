from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "clinic",
        "cta_type",
        "page_source",
        "city",
        "locality",
        "treatment",
        "problem",
        "created_at",
    )
    list_filter = ("cta_type", "page_source", "city", "created_at")
    search_fields = ("clinic__name",)
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in Lead._meta.fields]

    def has_add_permission(self, request):
        return False
