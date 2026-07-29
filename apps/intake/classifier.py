"""
Intake classification. This is a deterministic, keyword-based matcher — not an
LLM call — chosen deliberately for Phase 4:

  - It's honest: it never claims to understand free text it doesn't, and it
    never produces a "diagnosis," only a best-effort routing category.
  - It has no external dependency (no API key, no network call, no cost) so
    the intake flow works out of the box in this environment.

To upgrade to a real LLM later, replace the body of `classify()` with a call to
your model of choice (e.g. the Claude API) prompted to return one of the
existing `Problem` slugs — keep the same (problem, confidence, notes) return
shape and nothing else in the intake app needs to change.
"""

from dataclasses import dataclass, field

from apps.clinics.models import Problem

# Extra phrasing patients actually type, mapped to a Problem.slug already seeded
# by seed_roorkee. Keeps the matcher useful beyond exact problem names.
SYNONYMS = {
    "tooth-pain": ["hurts", "hurting", "ache", "aching", "throbbing", "pain in tooth", "toothache"],
    "bleeding-gums": ["gums bleed", "blood when brushing", "gum bleeding"],
    "tooth-sensitivity": ["sensitive", "sensitivity", "cold water hurts", "hurts when i drink"],
    "wisdom-tooth-pain": ["wisdom tooth", "back tooth pain", "molar pain at the back"],
    "bad-breath": ["bad breath", "smelly breath", "halitosis"],
    "gum-swelling": ["swollen gum", "gums are swollen", "puffy gum"],
    "cavity": ["hole in tooth", "black spot", "decay"],
    "broken-tooth": ["chipped", "broke my tooth", "cracked tooth", "fractured tooth"],
}


@dataclass
class ClassificationResult:
    problem: Problem | None
    confidence: float
    notes: str
    matched_treatments: list = field(default_factory=list)


def classify(problem_description: str, city=None) -> ClassificationResult:
    """
    Match free-text intake against known Problem categories by keyword overlap,
    scoped to `city` (Problem is city-scoped — see clinics.models.Problem). Falls
    back to matching across all cities if no city is given.
    """
    text = problem_description.lower().strip()
    if not text:
        return ClassificationResult(None, 0.0, "No description provided.")

    best_problem = None
    best_score = 0.0

    candidates = Problem.objects.filter(is_active=True)
    if city:
        candidates = candidates.filter(city=city)

    for problem in candidates:
        haystacks = [problem.name.lower()] + SYNONYMS.get(problem.slug, [])
        score = 0.0
        for phrase in haystacks:
            if phrase in text:
                # Longer/more specific phrase matches count for more than a single word.
                score = max(score, 0.9 if len(phrase.split()) > 1 else 0.6)
        if score > best_score:
            best_score = score
            best_problem = problem

    if not best_problem:
        return ClassificationResult(
            None, 0.0, "Could not confidently match a problem category from the description."
        )

    treatments = list(best_problem.suggested_treatment_categories.filter(is_active=True))
    notes = f"Matched '{best_problem.name}' via keyword overlap (confidence {best_score:.1f})."
    return ClassificationResult(best_problem, best_score, notes, treatments)
