from django.http import Http404
from django.shortcuts import render

from apps.analytics.models import PageView
from apps.analytics.utils import track_pageview
from apps.clinics.models import Clinic, ClinicFAQ, Problem, Treatment
from apps.seo import schema
from apps.seo.breadcrumbs import city_breadcrumbs, locality_breadcrumbs
from apps.seo.linking import nearby_localities

from .models import City, Locality


def _filter_clinics(request, base_qs):
    """Apply locality/treatment/verified/fee filters shared by city & locality pages."""
    locality_slug = request.GET.get("locality")
    treatment_slug = request.GET.get("treatment")
    verified_only = request.GET.get("verified") == "1"
    fee_max = request.GET.get("fee_max")

    if locality_slug:
        base_qs = base_qs.filter(locality__slug=locality_slug)
    if treatment_slug:
        base_qs = base_qs.filter(treatments__slug=treatment_slug)
    if fee_max:
        try:
            base_qs = base_qs.filter(consultation_fee__lte=int(fee_max))
        except ValueError:
            pass

    clinics = base_qs.distinct().select_related("locality", "city").prefetch_related(
        "treatments", "verification_records"
    )

    if verified_only:
        clinics = [c for c in clinics if c.is_verified]

    return clinics


def city_or_locality(request, rest):
    """
    Handles both:
      /dentist-in-roorkee/                -> city page
      /dentist-in-roorkee-civil-lines/     -> locality page

    `rest` is everything after 'dentist-in-'.
    """
    city = City.objects.filter(slug=rest, is_active=True).first()
    if city:
        return _city_detail(request, city)

    # Try to match rest as "<city_slug>-<locality_slug>"
    for city_candidate in City.objects.filter(is_active=True):
        prefix = f"{city_candidate.slug}-"
        if rest.startswith(prefix):
            locality_slug = rest[len(prefix):]
            locality = Locality.objects.filter(
                city=city_candidate, slug=locality_slug, is_active=True
            ).first()
            if locality:
                return _locality_detail(request, locality)

    raise Http404("Page not found")


def _city_detail(request, city):
    clinics = _filter_clinics(request, Clinic.objects.filter(city=city, is_active=True))
    localities = city.localities.filter(is_active=True)
    treatments = Treatment.objects.filter(city=city, is_active=True)
    problems = Problem.objects.filter(city=city, is_active=True)
    faqs = ClinicFAQ.objects.filter(city=city, clinic__isnull=True, locality__isnull=True)
    crumbs = city_breadcrumbs(city)

    track_pageview(request, PageView.PageType.CITY, page_slug=city.slug, city=city)

    context = {
        "city": city,
        "clinics": clinics,
        "localities": localities,
        "treatments": treatments,
        "problems": problems,
        "faqs": faqs,
        "city_crumbs": crumbs,
        "page_source": "city",
        "page_slug": city.slug,
        "meta_title": city.meta_title or f"Best Dentists in {city.name} | BestDentistIn",
        "meta_description": city.meta_description
        or f"Find verified dentists in {city.name}. Compare clinics by locality and treatment, and contact them instantly on WhatsApp or call.",
        "schema_jsonld": schema.to_json_ld(
            schema.breadcrumb_list_schema(request, crumbs),
            schema.item_list_schema(request, clinics),
        ),
    }
    return render(request, "locations/city_detail.html", context)


def _locality_detail(request, locality):
    clinics = _filter_clinics(
        request, Clinic.objects.filter(locality=locality, is_active=True)
    )
    treatments = Treatment.objects.filter(city=locality.city, is_active=True)[:8]
    problems = Problem.objects.filter(city=locality.city, is_active=True)[:8]
    faqs = ClinicFAQ.objects.filter(locality=locality, clinic__isnull=True)
    nearby = nearby_localities(locality)
    crumbs = locality_breadcrumbs(locality)

    track_pageview(
        request,
        PageView.PageType.LOCALITY,
        page_slug=locality.url_slug,
        city=locality.city,
        locality=locality,
    )

    context = {
        "city": locality.city,
        "locality": locality,
        "clinics": clinics,
        "treatments": treatments,
        "problems": problems,
        "faqs": faqs,
        "nearby_localities": nearby,
        "locality_crumbs": crumbs,
        "page_source": "locality",
        "page_slug": locality.url_slug,
        "meta_title": locality.meta_title or f"Dentists in {locality.name}, {locality.city.name} | BestDentistIn",
        "meta_description": locality.meta_description
        or f"Verified dentists and dental clinics in {locality.name}, {locality.city.name}. Contact clinics directly on WhatsApp or call.",
        "schema_jsonld": schema.to_json_ld(
            schema.breadcrumb_list_schema(request, crumbs),
            schema.item_list_schema(request, clinics),
        ),
    }
    return render(request, "locations/locality_detail.html", context)
