from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import render

from apps.analytics.models import PageView
from apps.clinics.models import Clinic, Problem, Treatment
from apps.leads.models import Lead
from apps.locations.models import City


@staff_member_required
def dashboard_home(request):
    total_leads = Lead.objects.count()
    whatsapp_leads = Lead.objects.filter(cta_type=Lead.CtaType.WHATSAPP).count()
    call_leads = Lead.objects.filter(cta_type=Lead.CtaType.CALL).count()
    total_pageviews = PageView.objects.count()
    overall_ctr = round(100 * total_leads / total_pageviews, 1) if total_pageviews else 0

    leads_by_page = (
        Lead.objects.values("page_source").annotate(total=Count("id")).order_by("-total")
    )
    top_clinics = (
        Lead.objects.values("clinic__name").annotate(total=Count("id")).order_by("-total")[:10]
    )
    recent_leads = Lead.objects.select_related("clinic", "city", "locality")[:20]

    context = {
        "total_leads": total_leads,
        "whatsapp_leads": whatsapp_leads,
        "call_leads": call_leads,
        "total_pageviews": total_pageviews,
        "overall_ctr": overall_ctr,
        "leads_by_page": leads_by_page,
        "top_clinics": top_clinics,
        "recent_leads": recent_leads,
        "total_clinics": Clinic.objects.filter(is_active=True).count(),
    }
    return render(request, "dashboard/home.html", context)


@staff_member_required
def leads_list(request):
    leads = Lead.objects.select_related("clinic", "city", "locality", "treatment", "problem")

    cta_type = request.GET.get("cta_type")
    if cta_type:
        leads = leads.filter(cta_type=cta_type)

    page_source = request.GET.get("page_source")
    if page_source:
        leads = leads.filter(page_source=page_source)

    context = {
        "leads": leads[:200],
        "cta_choices": Lead.CtaType.choices,
        "page_source_choices": Lead.PageSource.choices,
    }
    return render(request, "dashboard/leads_list.html", context)


@staff_member_required
def clinics_list(request):
    clinics = Clinic.objects.select_related("city", "locality").prefetch_related("verification_records")
    context = {"clinics": clinics}
    return render(request, "dashboard/clinics_list.html", context)


def _pageview_counts():
    """{(page_type, page_slug): views} for every page that's had at least one open."""
    rows = PageView.objects.values("page_type", "page_slug").annotate(total=Count("id"))
    return {(r["page_type"], r["page_slug"]): r["total"] for r in rows}


def _lead_counts():
    """{(page_source, page_slug): leads} for every page that's produced at least one CTA click."""
    rows = Lead.objects.values("page_source", "page_slug").annotate(total=Count("id"))
    return {(r["page_source"], r["page_slug"]): r["total"] for r in rows}


@staff_member_required
def pages_performance(request):
    """
    Top lead-generating pages + pages that get traffic but convert poorly — the two
    things an SEO/growth operator actually wants to know: what's working, and what's
    getting clicks from search but failing to turn into a WhatsApp/call lead.
    """
    views_by_page = _pageview_counts()
    leads_by_page = _lead_counts()

    all_keys = set(views_by_page) | set(leads_by_page)
    rows = []
    for key in all_keys:
        page_type, page_slug = key
        views = views_by_page.get(key, 0)
        leads = leads_by_page.get(key, 0)
        ctr = round(100 * leads / views, 1) if views else None
        rows.append(
            {
                "page_type": page_type,
                "page_slug": page_slug or "(none)",
                "views": views,
                "leads": leads,
                "ctr": ctr,
            }
        )

    top_leads = sorted(rows, key=lambda r: r["leads"], reverse=True)[:15]

    # "Traffic but weak conversion": pages with a meaningful number of views (>=3,
    # so a single visitor bounce doesn't skew the list) and zero or low CTR.
    weak_conversion = sorted(
        [r for r in rows if r["views"] >= 3],
        key=lambda r: (r["ctr"] if r["ctr"] is not None else 0),
    )[:15]

    context = {
        "top_leads": top_leads,
        "weak_conversion": weak_conversion,
    }
    return render(request, "dashboard/pages_performance.html", context)


@staff_member_required
def content_performance(request):
    """Views vs. leads vs. conversion, broken down by city, treatment, and problem."""

    def build_rows(model_cls, pv_field, lead_field):
        pv_counts = dict(
            PageView.objects.filter(**{f"{pv_field}__isnull": False})
            .values_list(pv_field)
            .annotate(total=Count("id"))
        )
        lead_counts = dict(
            Lead.objects.filter(**{f"{lead_field}__isnull": False})
            .values_list(lead_field)
            .annotate(total=Count("id"))
        )
        rows = []
        for obj in model_cls.objects.filter(is_active=True):
            views = pv_counts.get(obj.id, 0)
            leads = lead_counts.get(obj.id, 0)
            rows.append(
                {
                    "name": obj.name,
                    "url": obj.get_absolute_url(),
                    "views": views,
                    "leads": leads,
                    "ctr": round(100 * leads / views, 1) if views else None,
                }
            )
        return sorted(rows, key=lambda r: r["leads"], reverse=True)

    city_rows = []
    for city in City.objects.filter(is_active=True):
        views = PageView.objects.filter(city=city).count()
        leads = Lead.objects.filter(city=city).count()
        city_rows.append(
            {
                "name": city.name,
                "url": city.get_absolute_url(),
                "views": views,
                "leads": leads,
                "ctr": round(100 * leads / views, 1) if views else None,
            }
        )

    context = {
        "city_rows": sorted(city_rows, key=lambda r: r["leads"], reverse=True),
        "treatment_rows": build_rows(Treatment, "treatment_id", "treatment_id"),
        "problem_rows": build_rows(Problem, "problem_id", "problem_id"),
    }
    return render(request, "dashboard/content_performance.html", context)
