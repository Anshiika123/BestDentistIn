from django.conf import settings
from django.shortcuts import render

from apps.analytics.models import PageView
from apps.analytics.utils import track_pageview
from apps.clinics.models import Clinic, Problem, Treatment

from .utils import get_primary_city


def home(request):
    city = get_primary_city()

    featured_clinics = []
    localities = []
    if city:
        featured_clinics = (
            Clinic.objects.filter(city=city, is_active=True, is_featured=True)
            .select_related("locality")
            .prefetch_related("verification_records")[:6]
        )
        if not featured_clinics:
            featured_clinics = Clinic.objects.filter(city=city, is_active=True).select_related("locality")[:6]
        localities = city.localities.filter(is_active=True)

    treatments = Treatment.objects.filter(city=city, is_active=True)[:8] if city else Treatment.objects.none()
    problems = Problem.objects.filter(city=city, is_active=True)[:8] if city else Problem.objects.none()

    track_pageview(request, PageView.PageType.HOME, page_slug="home", city=city)

    context = {
        "city": city,
        "featured_clinics": featured_clinics,
        "localities": localities,
        "treatments": treatments,
        "problems": problems,
        "page_source": "home",
        "page_slug": "home",
        "meta_title": f"{settings.SITE_NAME} — Find Verified Dentists Near You",
        "meta_description": (
            "Find verified dentists in Roorkee and contact clinics instantly on "
            "WhatsApp or call. Compare clinics by locality and treatment."
        ),
    }
    return render(request, "core/home.html", context)
