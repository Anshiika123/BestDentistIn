"""Match an IntakeSession to a short list of relevant, active clinics."""

from apps.clinics.models import Clinic


def match_clinics(session, limit=5):
    """
    Priority: verified clinics offering the matched problem/treatment, in the
    patient's preferred locality if given, falling back to city-wide and then
    to any active clinic so a patient never sees an empty results page.
    """
    treatments = list(session.suggested_treatments.all())
    problem = session.problem_category

    base = Clinic.objects.filter(is_active=True).select_related("city", "locality")
    if session.preferred_locality:
        base = base.filter(city=session.preferred_locality.city)

    def _filter_by_relevance(qs):
        if treatments:
            qs = qs.filter(treatments__in=treatments)
        elif problem:
            qs = qs.filter(problems=problem)
        return qs.distinct()

    relevant = _filter_by_relevance(base)

    # Prefer clinics in the exact preferred locality, then top up from the rest of the city.
    ranked = []
    if session.preferred_locality:
        ranked.extend(relevant.filter(locality=session.preferred_locality))
    ranked.extend(c for c in relevant if c not in ranked)

    if len(ranked) < limit:
        # Widen: any active clinic in the same city/locality even without an exact
        # treatment/problem match, so results are never empty for a real query.
        fallback = base.exclude(id__in=[c.id for c in ranked])
        ranked.extend(fallback[: limit - len(ranked)])

    ranked = ranked[:limit]
    # Verified clinics first within the final shortlist.
    ranked.sort(key=lambda c: not c.is_verified)
    return ranked
