from django.contrib import admin

from .models import IntakeSession


@admin.register(IntakeSession)
class IntakeSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "problem_category",
        "urgency",
        "preferred_locality",
        "selected_clinic",
        "lead_created",
        "created_at",
    )
    list_filter = ("urgency", "patient_type", "lead_created", "source_channel")
    filter_horizontal = ("suggested_treatments", "matched_clinics")
    readonly_fields = [f.name for f in IntakeSession._meta.fields if f.name != "id"]

    def has_add_permission(self, request):
        return False
