from django.contrib import admin

from .models import Lead, LeadActivityLog, LeadNote

# Fields captured automatically by the click-tracking pipeline — never hand-edited.
CAPTURE_FIELDS = {
    "clinic", "city", "locality", "cta_type", "page_source", "page_slug", "cta_label",
    "treatment", "problem", "intake_session", "referrer_url", "user_agent", "ip_address",
    "utm_source", "utm_medium", "utm_campaign", "created_at",
}


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    readonly_fields = ("created_at",)


class LeadActivityLogInline(admin.TabularInline):
    model = LeadActivityLog
    extra = 0
    readonly_fields = [f.name for f in LeadActivityLog._meta.fields]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "clinic",
        "cta_type",
        "page_source",
        "status",
        "follow_up_type",
        "assigned_to",
        "created_at",
    )
    list_filter = ("cta_type", "page_source", "status", "follow_up_type", "city", "created_at")
    search_fields = ("clinic__name",)
    date_hierarchy = "created_at"
    autocomplete_fields = ["assigned_to"]
    readonly_fields = [f.name for f in Lead._meta.fields if f.name in CAPTURE_FIELDS]
    inlines = [LeadNoteInline, LeadActivityLogInline]

    def has_add_permission(self, request):
        return False


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ("lead", "author", "created_at")
    search_fields = ("note",)


@admin.register(LeadActivityLog)
class LeadActivityLogAdmin(admin.ModelAdmin):
    list_display = ("lead", "action", "actor", "from_value", "to_value", "created_at")
    list_filter = ("action",)

    def has_add_permission(self, request):
        return False
