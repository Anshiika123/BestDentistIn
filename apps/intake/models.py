import uuid

from django.db import models


class IntakeSession(models.Model):
    """
    One AI-intake conversation. Phase 4 intentionally does not diagnose —
    `problem_category`/`suggested_treatments` are a best-effort classification
    used only to route the patient to relevant clinics, never presented as a
    medical opinion (see apps.intake.classifier and the disclaimer shown on
    every intake template).
    """

    class Urgency(models.TextChoices):
        LOW = "low", "Mild — can wait a few days"
        MEDIUM = "medium", "Moderate — would like to see someone soon"
        HIGH = "high", "Severe — need to see someone urgently"

    class Duration(models.TextChoices):
        JUST_STARTED = "just_started", "Just started (today)"
        FEW_DAYS = "few_days", "A few days"
        ONE_WEEK_PLUS = "week_plus", "A week or more"
        CHRONIC = "chronic", "Ongoing / recurring"

    class PatientType(models.TextChoices):
        NEW = "new", "New Patient"
        EXISTING = "existing", "Existing Patient"

    class AgeGroup(models.TextChoices):
        CHILD = "child", "Child (under 12)"
        TEEN = "teen", "Teen (12-19)"
        ADULT = "adult", "Adult (20-59)"
        SENIOR = "senior", "Senior (60+)"

    class SourceChannel(models.TextChoices):
        WEB_CHAT = "web_chat", "Website"
        WHATSAPP = "whatsapp", "WhatsApp"  # future
        VOICE = "voice", "Voice"  # future

    session_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # --- raw user input ---
    problem_description = models.TextField(help_text="Patient's own words describing the issue.")
    urgency = models.CharField(max_length=10, choices=Urgency.choices)
    duration = models.CharField(max_length=20, choices=Duration.choices)
    patient_type = models.CharField(max_length=10, choices=PatientType.choices)
    preferred_locality = models.ForeignKey(
        "locations.Locality", related_name="intake_sessions", on_delete=models.SET_NULL, null=True, blank=True
    )
    preferred_time = models.CharField(max_length=100, blank=True, help_text="Free text, e.g. 'weekday evenings'.")
    age_group = models.CharField(max_length=10, choices=AgeGroup.choices, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    language_preference = models.CharField(max_length=50, blank=True)

    # --- classification / routing result ---
    problem_category = models.ForeignKey(
        "clinics.Problem", related_name="intake_sessions", on_delete=models.SET_NULL, null=True, blank=True
    )
    suggested_treatments = models.ManyToManyField("clinics.Treatment", blank=True, related_name="intake_sessions")
    matched_clinics = models.ManyToManyField("clinics.Clinic", blank=True, related_name="intake_matches")
    selected_clinic = models.ForeignKey(
        "clinics.Clinic", related_name="intake_selections", on_delete=models.SET_NULL, null=True, blank=True
    )
    confidence_score = models.FloatField(
        null=True, blank=True, help_text="0-1 keyword-match confidence from the classifier. Not a medical score."
    )
    ai_notes = models.TextField(blank=True, help_text="Internal notes from the classifier for the clinic/ops team.")

    lead_created = models.BooleanField(default=False)
    source_channel = models.CharField(max_length=10, choices=SourceChannel.choices, default=SourceChannel.WEB_CHAT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Intake #{self.id} ({self.get_urgency_display()}, {self.created_at:%Y-%m-%d %H:%M})"
