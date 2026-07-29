from .models import PageView

UTM_FIELDS = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")


def track_pageview(request, page_type, page_slug="", **kwargs):
    """
    Log a page open for analytics. Call from public detail/list views only —
    never from the dashboard, admin, or lead-tracking redirect views.

    kwargs may include: city, locality, clinic, treatment, problem (model instances).
    """
    utm = {field: request.GET.get(field, "")[:100] for field in UTM_FIELDS}

    # Remember the first UTM params seen this session so a WhatsApp/Call click a few
    # pages into the visit can still be attributed back to the original campaign
    # (see apps.leads.views._resolve_utm).
    if any(utm.values()):
        request.session["utm"] = {k: v for k, v in utm.items() if v}

    PageView.objects.create(
        page_type=page_type,
        page_slug=page_slug,
        path=request.path[:300],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        **utm,
        **kwargs,
    )
