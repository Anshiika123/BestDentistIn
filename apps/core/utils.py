from django.conf import settings

from apps.locations.models import City


def get_primary_city():
    """
    Phase 1/2 are single-city (Roorkee). Centralizing this lookup means the rest
    of the codebase never hardcodes the city slug directly, so adding a second
    city later is a data change, not a code change.
    """
    return City.objects.filter(slug=settings.PRIMARY_CITY_SLUG, is_active=True).first()
