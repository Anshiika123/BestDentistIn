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

    referrer_url = models.CharField(max_length=300, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["clinic", "created_at"]),
            models.Index(fields=["page_source", "created_at"]),
            models.Index(fields=["page_source", "page_slug", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_cta_type_display()} lead for {self.clinic.name} ({self.created_at:%Y-%m-%d %H:%M})"
