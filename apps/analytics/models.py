from django.db import models


class PageView(models.Model):
    """
    Analytics-only record of a page open. Never a lead — CTA clicks (WhatsApp/Call)
    are recorded separately in apps.leads.Lead. Kept deliberately generic (string
    page_type/page_slug rather than FKs to every possible page model) so new page
    types — new cities, new treatment/problem categories — don't require schema
    changes here.
    """

    class PageType(models.TextChoices):
        HOME = "home", "Home"
        CITY = "city", "City Page"
        LOCALITY = "locality", "Locality Page"
        CLINIC = "clinic", "Clinic Profile"
        TREATMENT = "treatment", "Treatment Page"
        PROBLEM = "problem", "Problem Page"
        BLOG = "blog", "Blog"

    page_type = models.CharField(max_length=20, choices=PageType.choices)
    page_slug = models.CharField(max_length=220, blank=True)
    path = models.CharField(max_length=300, blank=True)

    city = models.ForeignKey(
        "locations.City", related_name="page_views", on_delete=models.SET_NULL, null=True, blank=True
    )
    locality = models.ForeignKey(
        "locations.Locality", related_name="page_views", on_delete=models.SET_NULL, null=True, blank=True
    )
    clinic = models.ForeignKey(
        "clinics.Clinic", related_name="page_views", on_delete=models.SET_NULL, null=True, blank=True
    )
    treatment = models.ForeignKey(
        "clinics.Treatment", related_name="page_views", on_delete=models.SET_NULL, null=True, blank=True
    )
    problem = models.ForeignKey(
        "clinics.Problem", related_name="page_views", on_delete=models.SET_NULL, null=True, blank=True
    )

    referrer = models.CharField(max_length=300, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    utm_term = models.CharField(max_length=100, blank=True)
    utm_content = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["page_type", "page_slug", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"View: {self.page_type}/{self.page_slug} ({self.created_at:%Y-%m-%d %H:%M})"
