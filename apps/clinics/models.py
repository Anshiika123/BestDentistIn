import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.locations.models import City, Locality


class Treatment(models.Model):
    """
    A dental treatment/procedure, e.g. Root Canal, Braces. City-scoped so a
    second city can carry its own fee range/copy for the same treatment (e.g.
    "braces cost in Dehradun" as its own indexable page) instead of one
    city-agnostic page. URLs stay flat (/treatments/<slug>/, unchanged) and are
    resolved against the primary city for now — see README for the multi-city
    URL disambiguation this will need once a second city is actually added.
    """

    city = models.ForeignKey(City, related_name="treatments", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, help_text="e.g. root-canal")
    short_description = models.CharField(max_length=300, blank=True)

    explanation = models.TextField(blank=True, help_text="Simple explanation of the treatment.")
    symptoms = models.TextField(blank=True, help_text="Symptoms that suggest this treatment is needed.")
    when_to_visit = models.TextField(blank=True)
    what_to_expect = models.TextField(blank=True)
    fee_range_min = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated fee, INR")
    fee_range_max = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated fee, INR")

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    related_problems = models.ManyToManyField("Problem", blank=True, related_name="related_treatments")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("city", "slug")]

    def __str__(self):
        return f"{self.name} ({self.city.name})"

    def get_absolute_url(self):
        return reverse("clinics:treatment_detail", kwargs={"slug": self.slug})


class Problem(models.Model):
    """A dental problem/symptom, e.g. Tooth Pain, Bleeding Gums. City-scoped — see Treatment."""

    city = models.ForeignKey(City, related_name="problems", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, help_text="e.g. tooth-pain")
    short_description = models.CharField(max_length=300, blank=True)

    symptom_explanation = models.TextField(blank=True)
    possible_causes = models.TextField(blank=True)
    when_urgent_care_needed = models.TextField(blank=True)
    suggested_treatment_categories = models.ManyToManyField(
        Treatment, blank=True, related_name="suggested_for_problems"
    )

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("city", "slug")]

    def __str__(self):
        return f"{self.name} ({self.city.name})"

    def get_absolute_url(self):
        return reverse("clinics:problem_detail", kwargs={"slug": self.slug})


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, help_text="e.g. dr-sharma-dental-care-roorkee")

    city = models.ForeignKey(City, related_name="clinics", on_delete=models.CASCADE)
    locality = models.ForeignKey(Locality, related_name="clinics", on_delete=models.CASCADE)

    address = models.CharField(max_length=300)
    map_embed_url = models.URLField(blank=True, help_text="Google Maps embed URL placeholder")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    phone_number = models.CharField(max_length=20, help_text="Local format for display, e.g. 01332-123456")
    whatsapp_number = models.CharField(
        max_length=20, help_text="International format without '+' for wa.me links, e.g. 919876543210"
    )

    timings = models.CharField(max_length=200, help_text="e.g. Mon-Sat 9:00 AM - 7:00 PM")
    consultation_fee = models.PositiveIntegerField(null=True, blank=True, help_text="INR, optional")

    about = models.TextField(blank=True)
    logo = models.ImageField(upload_to="clinics/logos/", blank=True, null=True)
    cover_photo = models.ImageField(upload_to="clinics/covers/", blank=True, null=True)

    treatments = models.ManyToManyField(Treatment, blank=True, related_name="clinics")
    problems = models.ManyToManyField(Problem, blank=True, related_name="clinics")

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("clinics:clinic_detail", kwargs={"slug": self.slug})

    @property
    def latest_verification(self):
        return self.verification_records.order_by("-last_verified_at").first()

    @property
    def is_verified(self):
        v = self.latest_verification
        if not v or not v.is_verified or not v.phone_confirmed or not v.timings_confirmed:
            return False
        if not v.last_verified_at:
            return False
        freshness = getattr(settings, "VERIFICATION_FRESHNESS_DAYS", 180)
        return v.last_verified_at >= timezone.now() - datetime.timedelta(days=freshness)

    @property
    def whatsapp_link(self):
        return f"https://wa.me/{self.whatsapp_number}"

    @property
    def tel_link(self):
        return f"tel:{self.phone_number}"


class ClinicPhoto(models.Model):
    """Clinic gallery image. Replaces the placeholder gallery boxes on the clinic page when present."""

    clinic = models.ForeignKey(Clinic, related_name="photos", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="clinics/gallery/")
    caption = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or f"Photo of {self.clinic.name}"


class Dentist(models.Model):
    clinic = models.ForeignKey(Clinic, related_name="dentists", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    qualification = models.CharField(max_length=200, help_text="e.g. BDS, MDS (Orthodontics)")
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="dentists/photos/", blank=True, null=True)
    is_primary = models.BooleanField(default=False, help_text="Primary dentist shown on clinic profile.")

    class Meta:
        ordering = ["-is_primary", "name"]

    def __str__(self):
        return f"Dr. {self.name}"


class VerificationRecord(models.Model):
    class Source(models.TextChoices):
        PHONE_CALL = "phone_call", "Phone Call"
        WHATSAPP = "whatsapp", "WhatsApp"
        GOOGLE_PROFILE = "google_profile", "Google Business Profile"
        WEBSITE = "website", "Clinic Website"
        IN_PERSON = "in_person", "In Person Visit"
        OTHER = "other", "Other"

    clinic = models.ForeignKey(Clinic, related_name="verification_records", on_delete=models.CASCADE)

    is_verified = models.BooleanField(default=False)
    verification_source = models.CharField(max_length=20, choices=Source.choices, default=Source.PHONE_CALL)
    last_verified_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    proof_website = models.URLField(blank=True)
    proof_google_profile = models.URLField(blank=True)
    phone_confirmed = models.BooleanField(default=False)
    timings_confirmed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_verified_at"]

    def __str__(self):
        return f"Verification for {self.clinic.name} on {self.last_verified_at:%Y-%m-%d}"


class ClinicFAQ(models.Model):
    clinic = models.ForeignKey(Clinic, related_name="faqs", on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, related_name="faqs", on_delete=models.CASCADE, null=True, blank=True)
    locality = models.ForeignKey(Locality, related_name="faqs", on_delete=models.CASCADE, null=True, blank=True)
    treatment = models.ForeignKey(Treatment, related_name="faqs", on_delete=models.CASCADE, null=True, blank=True)
    problem = models.ForeignKey(Problem, related_name="faqs", on_delete=models.CASCADE, null=True, blank=True)

    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class Review(models.Model):
    """Placeholder review model — not user-submittable in Phase 1."""

    clinic = models.ForeignKey(Clinic, related_name="reviews", on_delete=models.CASCADE)
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5, help_text="1-5")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} ({self.rating}★) - {self.clinic.name}"
