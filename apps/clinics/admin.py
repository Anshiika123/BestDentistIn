from django.contrib import admin

from .models import Clinic, ClinicFAQ, Dentist, Problem, Review, Treatment, VerificationRecord


class DentistInline(admin.TabularInline):
    model = Dentist
    extra = 1


class VerificationInline(admin.TabularInline):
    model = VerificationRecord
    extra = 0


class ClinicFAQInline(admin.TabularInline):
    model = ClinicFAQ
    extra = 0
    fk_name = "clinic"


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "locality",
        "phone_number",
        "is_active",
        "is_featured",
        "verified_badge",
    )
    list_filter = ("city", "locality", "is_active", "is_featured")
    search_fields = ("name", "address", "phone_number", "whatsapp_number")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("treatments", "problems")
    inlines = [DentistInline, VerificationInline, ClinicFAQInline]

    @admin.display(boolean=True, description="Verified")
    def verified_badge(self, obj):
        return obj.is_verified


@admin.register(Dentist)
class DentistAdmin(admin.ModelAdmin):
    list_display = ("name", "clinic", "qualification", "experience_years", "is_primary")
    list_filter = ("clinic__city",)


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("related_problems",)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("suggested_treatment_categories",)


@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ("clinic", "is_verified", "verification_source", "last_verified_at")
    list_filter = ("is_verified", "verification_source")


@admin.register(ClinicFAQ)
class ClinicFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "clinic", "city", "locality", "treatment", "problem", "order")
    list_filter = ("city", "treatment", "problem")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("clinic", "author_name", "rating", "is_published", "created_at")
    list_filter = ("is_published", "rating")
