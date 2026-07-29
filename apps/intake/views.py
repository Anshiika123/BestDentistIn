from django.shortcuts import get_object_or_404, redirect, render

from apps.core.utils import get_primary_city
from apps.locations.models import Locality

from .classifier import classify
from .models import IntakeSession
from .routing import match_clinics


def intake_start(request):
    if request.method == "POST":
        description = request.POST.get("problem_description", "").strip()
        urgency = request.POST.get("urgency", IntakeSession.Urgency.LOW)
        duration = request.POST.get("duration", IntakeSession.Duration.JUST_STARTED)
        patient_type = request.POST.get("patient_type", IntakeSession.PatientType.NEW)
        locality_id = request.POST.get("preferred_locality") or None
        preferred_time = request.POST.get("preferred_time", "").strip()[:100]
        age_group = request.POST.get("age_group", "")
        phone = request.POST.get("phone", "").strip()[:20]
        language_preference = request.POST.get("language_preference", "").strip()[:50]

        if not description:
            return render(
                request,
                "intake/start.html",
                {
                    "localities": Locality.objects.filter(is_active=True).select_related("city"),
                    "error": "Please describe what you're experiencing so we can help route you to the right clinic.",
                    "form_data": request.POST,
                },
            )

        preferred_locality = Locality.objects.filter(id=locality_id).first() if locality_id else None

        session = IntakeSession.objects.create(
            problem_description=description[:2000],
            urgency=urgency if urgency in IntakeSession.Urgency.values else IntakeSession.Urgency.LOW,
            duration=duration if duration in IntakeSession.Duration.values else IntakeSession.Duration.JUST_STARTED,
            patient_type=patient_type if patient_type in IntakeSession.PatientType.values else IntakeSession.PatientType.NEW,
            preferred_locality=preferred_locality,
            preferred_time=preferred_time,
            age_group=age_group if age_group in IntakeSession.AgeGroup.values else "",
            phone=phone,
            language_preference=language_preference,
        )

        classify_city = preferred_locality.city if preferred_locality else get_primary_city()
        result = classify(description, city=classify_city)
        session.problem_category = result.problem
        session.confidence_score = result.confidence
        session.ai_notes = result.notes
        if result.matched_treatments:
            session.suggested_treatments.set(result.matched_treatments)
        session.save()

        matched = match_clinics(session)
        session.matched_clinics.set(matched)

        return redirect("intake:results", session_key=session.session_key)

    context = {"localities": Locality.objects.filter(is_active=True).select_related("city")}
    return render(request, "intake/start.html", context)


def intake_results(request, session_key):
    session = get_object_or_404(
        IntakeSession.objects.select_related("problem_category", "preferred_locality"), session_key=session_key
    )
    clinics = session.matched_clinics.select_related("city", "locality").prefetch_related(
        "treatments", "verification_records"
    )

    context = {
        "session": session,
        "clinics": clinics,
        "page_source": "intake",
        "page_slug": str(session.session_key),
    }
    return render(request, "intake/results.html", context)
