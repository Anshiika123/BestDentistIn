"""
Breadcrumb trail builders. Each returns a list of (label, url|None) tuples
consumed by both templates/partials/breadcrumbs.html (visual nav) and
seo.schema.breadcrumb_list_schema (BreadcrumbList JSON-LD) — one source of
truth for both. "Home" is prepended by the template, not here.
"""

from django.urls import reverse


def city_breadcrumbs(city):
    return [(f"Dentists in {city.name}", None)]


def locality_breadcrumbs(locality):
    return [
        (f"Dentists in {locality.city.name}", locality.city.get_absolute_url()),
        (locality.name, None),
    ]


def clinic_breadcrumbs(clinic):
    return [
        (f"Dentists in {clinic.city.name}", clinic.city.get_absolute_url()),
        (clinic.locality.name, clinic.locality.get_absolute_url()),
        (clinic.name, None),
    ]


def treatment_breadcrumbs(treatment, city=None):
    crumbs = []
    if city:
        crumbs.append((f"Dentists in {city.name}", city.get_absolute_url()))
    crumbs.append((treatment.name, None))
    return crumbs


def problem_breadcrumbs(problem, city=None):
    crumbs = []
    if city:
        crumbs.append((f"Dentists in {city.name}", city.get_absolute_url()))
    crumbs.append((problem.name, None))
    return crumbs


def blog_list_breadcrumbs():
    return [("Blog", None)]


def blog_detail_breadcrumbs(post):
    crumbs = [("Blog", reverse("content:blog_list"))]
    if post.category:
        crumbs.append((post.category.name, f"{reverse('content:blog_list')}?category={post.category.slug}"))
    crumbs.append((post.title, None))
    return crumbs
