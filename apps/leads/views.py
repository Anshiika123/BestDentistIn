from urllib.parse import quote

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from apps.clinics.models import Clinic, Problem, Treatment

from .models import Lead

UTM_FIELDS = ("utm_source", "utm_medium", "utm_campaign")

DEFAULT_CTA_LABELS = {
    Lead.CtaType.WHATSAPP: "WhatsApp Now",
    Lead.CtaType.CALL: "Call Now",
}


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _resolve_utm(request):
    """
    Prefer UTM params on the click itself; fall back to whatever the visitor's
    session picked up from their landing page (set by analytics.track_pageview),
    so a click a few pages into the visit still attributes to the original campaign.
    """
    session_utm = request.session.get("utm", {})
    return {field: request.GET.get(field, "") or session_utm.get(field, "") for field in UTM_FIELDS}


def _resolve_context(request, clinic):
    page_source = request.GET.get("source", Lead.PageSource.CLINIC)
    if page_source not in Lead.PageSource.values:
        page_source = Lead.PageSource.CLINIC

    treatment = None
    treatment_slug = request.GET.get("treatment")
    if treatment_slug:
        treatment = Treatment.objects.filter(slug=treatment_slug).first()

    problem = None
    problem_slug = request.GET.get("problem")
    if problem_slug:
        problem = Problem.objects.filter(slug=problem_slug).first()

    page_slug = request.GET.get("page_slug", "")[:220]

    return page_source, treatment, problem, page_slug


def _build_whatsapp_message(clinic, page_source, treatment, problem):
    base = f"Hi, I found {clinic.name} on BestDentistIn"
    if treatment:
        return f"{base} and want to book an appointment for {treatment.name} in {clinic.city.name}."
    if problem:
        return f"{base} and want to book an appointment for {problem.name.lower()} in {clinic.city.name}."
    if page_source == Lead.PageSource.CLINIC:
        return f"{base} and want to book an appointment at your clinic in {clinic.locality.name}, {clinic.city.name}."
    return f"{base} and want to book an appointment in {clinic.city.name}."


def _log_lead(request, clinic, cta_type, page_source, treatment, problem, page_slug):
    cta_label = request.GET.get("label", "")[:100] or DEFAULT_CTA_LABELS.get(cta_type, "")
    utm = _resolve_utm(request)

    Lead.objects.create(
        clinic=clinic,
        city=clinic.city,
        locality=clinic.locality,
        cta_type=cta_type,
        page_source=page_source,
        page_slug=page_slug,
        cta_label=cta_label,
        treatment=treatment,
        problem=problem,
        referrer_url=request.META.get("HTTP_REFERER", "")[:300],
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        ip_address=_client_ip(request),
        **utm,
    )


def track_whatsapp(request, clinic_slug):
    clinic = get_object_or_404(Clinic, slug=clinic_slug, is_active=True)
    page_source, treatment, problem, page_slug = _resolve_context(request, clinic)
    _log_lead(request, clinic, Lead.CtaType.WHATSAPP, page_source, treatment, problem, page_slug)

    message = _build_whatsapp_message(clinic, page_source, treatment, problem)
    url = f"https://wa.me/{clinic.whatsapp_number}?text={quote(message)}"
    return HttpResponseRedirect(url)


def track_call(request, clinic_slug):
    clinic = get_object_or_404(Clinic, slug=clinic_slug, is_active=True)
    page_source, treatment, problem, page_slug = _resolve_context(request, clinic)
    _log_lead(request, clinic, Lead.CtaType.CALL, page_source, treatment, problem, page_slug)

    # HttpResponseRedirect rejects non-http(s)/ftp schemes as "unsafe", but tel: is
    # exactly what we want here — build the redirect response manually instead.
    response = HttpResponse(status=302)
    response["Location"] = f"tel:{clinic.phone_number}"
    return response
