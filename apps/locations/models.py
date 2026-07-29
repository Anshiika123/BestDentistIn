from django.db import models
from django.urls import reverse


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, help_text="e.g. roorkee")
    state = models.CharField(max_length=100, default="Uttarakhand")

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    intro_content = models.TextField(
        blank=True,
        help_text="SEO intro paragraph(s) shown on the city landing page.",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("locations:city_or_locality", kwargs={"rest": self.slug})


class Locality(models.Model):
    city = models.ForeignKey(City, related_name="localities", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, help_text="e.g. civil-lines")

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    intro_content = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Localities"
        unique_together = ("city", "slug")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.city.name}"

    @property
    def url_slug(self):
        """Slug used in the combined locality URL: dentist-in-<city>-<locality>."""
        return f"dentist-in-{self.city.slug}-{self.slug}"

    def get_absolute_url(self):
        return reverse("locations:city_or_locality", kwargs={"rest": f"{self.city.slug}-{self.slug}"})
