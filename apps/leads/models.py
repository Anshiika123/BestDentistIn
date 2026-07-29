from django.db import models

from apps.clinics.models import Clinic, Problem, Treatment
from apps.locations.models import City, Locality


class Lead(models.Model):
    class CtaType(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        CALL = "call", "Call"

    class PageSource(models.TextChoices):
        HOME = "home", "Home"
        CITY = "city", "City Page"
        LOCALITY = "locality", "Locality Page"
        CLINIC = "clinic", "Clinic Profile"
        TREATMENT = "treatment", "Treatment Page"
        PROBLEM = "problem", "Problem Page"
        BLOG = "blog", "Blog"
        INTAKE = "intake", "AI Intake"

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        SCHEDULED = "scheduled", "Appointment Scheduled"
        VISITED = "visited", "Visited"
        CLOSED = "closed", "Closed"
        NOT_REACHABLE = "not_reachable", "Not Reachable"
        MISSED = "missed", "Missed"

    class FollowUp(models.TextChoices):
        NONE = "none", "No Follow-up Needed"
        TODAY = "today", "Follow Up Today"
        TOMORROW = "tomorrow", "Follow Up Tomorrow"
        LATER = "later", "Follow Up Later"

    clinic = models.ForeignKey(Clinic, related_name="leads", on_delete=models.CASCADE)
    city = models.ForeignKey(City, related_name="leads", on_delete=models.SET_NULL, null=True, blank=True)
    locality = models.ForeignKey(Locality, related_name="leads", on_delete=models.SET_NULL, null=True, blank=True)

    cta_type = models.CharField(max_length=10, choices=CtaType.choices)
    page_source = models.CharField(max_length=20, choices=PageSource.choices)
    page_slug = models.CharField(
        max_length=220, blank=True, help_text="Slug of the page the click originated from, e.g. the treatment or clinic slug."
    )
    cta_label = models.CharField(max_length=100, blank=True, help_text="Button text/context, e.g. 'WhatsApp Now'.")

    treatment = models.ForeignKey(
        Treatment, related_name="leads", on_delete=models.SET_NULL, null=True, blank=True
    )
    problem = models.ForeignKey(Problem, related_name="leads", on_delete=models.SET_NULL, null=True, blank=True)
    intake_session = models.ForeignKey(
        "intake.IntakeSession", related_name="leads", on_delete=models.SET_NULL, null=True, blank=True
    )

    referrer_url = models.CharField(max_length=300, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    # --- Clinic SaaS workflow (Phase 3) ---
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    follow_up_type = models.CharField(max_length=10, choices=FollowUp.choices, default=FollowUp.NONE)
    follow_up_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        "accounts.ClinicUser", related_name="assigned_leads", on_delete=models.SET_NULL, null=True, blank=True
    )
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    missed_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. 'Patient did not answer', 'Clinic did not respond in time'.",
    )
    contact_number = models.CharField(max_length=20, blank=True, help_text="Captured from intake, if provided.")
    message = models.TextField(blank=True, help_text="Free-text message captured from intake, if provided.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["clinic", "created_at"]),
            models.Index(fields=["page_source", "created_at"]),
            models.Index(fields=["page_source", "page_slug", "created_at"]),
            models.Index(fields=["clinic", "status"]),
            models.Index(fields=["clinic", "follow_up_date"]),
        ]

    def __str__(self):
        return f"{self.get_cta_type_display()} lead for {self.clinic.name} ({self.created_at:%Y-%m-%d %H:%M})"


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, related_name="notes", on_delete=models.CASCADE)
    author = models.ForeignKey(
        "accounts.ClinicUser", related_name="notes", on_delete=models.SET_NULL, null=True, blank=True
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on lead #{self.lead_id} ({self.created_at:%Y-%m-%d %H:%M})"


class LeadActivityLog(models.Model):
    """Append-only audit trail: status changes, assignment changes, notes added."""

    class Action(models.TextChoices):
        STATUS_CHANGED = "status_changed", "Status Changed"
        FOLLOW_UP_SET = "follow_up_set", "Follow-up Set"
        ASSIGNED = "assigned", "Assigned"
        NOTE_ADDED = "note_added", "Note Added"
        CONTACTED = "contacted", "Marked Contacted"

    lead = models.ForeignKey(Lead, related_name="activity_log", on_delete=models.CASCADE)
    actor = models.ForeignKey(
        "accounts.ClinicUser", related_name="activity_entries", on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    from_value = models.CharField(max_length=100, blank=True)
    to_value = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Lead activity log"

    def __str__(self):
        return f"{self.get_action_display()} on lead #{self.lead_id}"
