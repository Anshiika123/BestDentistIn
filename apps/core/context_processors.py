from django.conf import settings


def site_context(request):
    from apps.clinics.models import Treatment
    from apps.locations.models import Locality

    return {
        "SITE_NAME": settings.SITE_NAME,
        "PRIMARY_CITY_SLUG": settings.PRIMARY_CITY_SLUG,
        "footer_localities": Locality.objects.filter(
            city__slug=settings.PRIMARY_CITY_SLUG, is_active=True
        ).select_related("city")[:8],
        "footer_treatments": Treatment.objects.filter(
            city__slug=settings.PRIMARY_CITY_SLUG, is_active=True
        )[:8],
    }
