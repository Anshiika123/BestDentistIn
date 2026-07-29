from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.clinics.models import Clinic, Problem, Treatment
from apps.content.models import BlogPost
from apps.locations.models import City, Locality


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ["home"]

    def location(self, item):
        return reverse(item)


class CitySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return City.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class LocalitySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Locality.objects.filter(is_active=True).select_related("city")

    def lastmod(self, obj):
        return obj.updated_at


class TreatmentSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Treatment.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class ProblemSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Problem.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class ClinicSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Clinic.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "cities": CitySitemap,
    "localities": LocalitySitemap,
    "treatments": TreatmentSitemap,
    "problems": ProblemSitemap,
    "clinics": ClinicSitemap,
    "blog": BlogPostSitemap,
}
