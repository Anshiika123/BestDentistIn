"""
Internal linking engine. Centralizes "what should this page link to next" so the
same rules apply consistently across templates instead of being re-derived ad hoc
in every view. City-agnostic — nothing here assumes Roorkee is the only city.
"""


def nearby_localities(locality, limit=4):
    return (
        locality.city.localities.filter(is_active=True)
        .exclude(id=locality.id)
        .select_related("city")[:limit]
    )


def nearby_clinics(clinic, limit=4):
    from apps.clinics.models import Clinic

    same_locality = list(
        Clinic.objects.filter(locality=clinic.locality, is_active=True)
        .exclude(id=clinic.id)
        .select_related("locality")[:limit]
    )
    if len(same_locality) >= limit:
        return same_locality

    same_city = Clinic.objects.filter(city=clinic.city, is_active=True).exclude(
        id__in=[clinic.id, *[c.id for c in same_locality]]
    ).select_related("locality")[: limit - len(same_locality)]

    return same_locality + list(same_city)


def related_blog_posts_for_treatment(treatment, limit=3):
    from apps.content.models import BlogPost

    return (
        BlogPost.objects.filter(is_published=True, category__treatments=treatment)
        .select_related("category")
        .distinct()[:limit]
    )


def related_blog_posts_for_problem(problem, limit=3):
    from apps.content.models import BlogPost

    return (
        BlogPost.objects.filter(is_published=True, category__problems=problem)
        .select_related("category")
        .distinct()[:limit]
    )


def related_pages_for_blog_post(post, limit=4):
    """Treatment/problem pages linked to the post's category — for a 'keep reading' block."""
    if not post.category:
        return [], []
    treatments = post.category.treatments.filter(is_active=True)[:limit]
    problems = post.category.problems.filter(is_active=True)[:limit]
    return treatments, problems
