from django.shortcuts import get_object_or_404, render

from apps.analytics.models import PageView
from apps.analytics.utils import track_pageview
from apps.seo import schema
from apps.seo.breadcrumbs import clinic_breadcrumbs, problem_breadcrumbs, treatment_breadcrumbs
from apps.seo.linking import (
    nearby_clinics,
    related_blog_posts_for_problem,
    related_blog_posts_for_treatment,
)

from .models import Clinic, ClinicFAQ, Problem, Treatment


def clinic_detail(request, slug):
    clinic = get_object_or_404(
        Clinic.objects.select_related("city", "locality").prefetch_related(
            "dentists", "treatments", "problems", "verification_records", "faqs", "reviews"
        ),
        slug=slug,
        is_active=True,
    )
    faqs = clinic.faqs.all()
    related_treatments = clinic.treatments.filter(is_active=True)
    related_problems = clinic.problems.filter(is_active=True)
    nearby = nearby_clinics(clinic)
    crumbs = clinic_breadcrumbs(clinic)

    track_pageview(
        request,
        PageView.PageType.CLINIC,
        page_slug=clinic.slug,
        city=clinic.city,
        locality=clinic.locality,
        clinic=clinic,
    )

    context = {
        "clinic": clinic,
        "city": clinic.city,
        "locality": clinic.locality,
        "primary_dentist": clinic.dentists.filter(is_primary=True).first() or clinic.dentists.first(),
        "faqs": faqs,
        "related_treatments": related_treatments,
        "related_problems": related_problems,
        "nearby_clinics": nearby,
        "clinic_crumbs": crumbs,
        "page_source": "clinic",
        "page_slug": clinic.slug,
        "meta_title": clinic.meta_title or f"{clinic.name} — {clinic.locality.name}, {clinic.city.name} | BestDentistIn",
        "meta_description": clinic.meta_description
        or f"{clinic.name} in {clinic.locality.name}, {clinic.city.name}. View timings, treatments and contact directly on WhatsApp or call.",
        "schema_jsonld": schema.to_json_ld(
            schema.breadcrumb_list_schema(request, crumbs),
            schema.local_business_schema(request, clinic),
            schema.faq_page_schema(faqs),
        ),
    }
    return render(request, "clinics/clinic_detail.html", context)


def treatment_detail(request, slug):
    treatment = get_object_or_404(Treatment, slug=slug, is_active=True)
    clinics = (
        treatment.clinics.filter(is_active=True)
        .select_related("city", "locality")
        .prefetch_related("verification_records")
    )
    faqs = ClinicFAQ.objects.filter(treatment=treatment, clinic__isnull=True)
    related_problems = treatment.related_problems.filter(is_active=True)
    related_posts = related_blog_posts_for_treatment(treatment)
    city = clinics[0].city if clinics else None
    crumbs = treatment_breadcrumbs(treatment, city=city)

    track_pageview(request, PageView.PageType.TREATMENT, page_slug=treatment.slug, treatment=treatment, city=city)

    context = {
        "treatment": treatment,
        "clinics": clinics,
        "faqs": faqs,
        "related_problems": related_problems,
        "related_posts": related_posts,
        "treatment_crumbs": crumbs,
        "page_source": "treatment",
        "page_slug": treatment.slug,
        "meta_title": treatment.meta_title or f"{treatment.name} in Roorkee — Cost, Process & Clinics | BestDentistIn",
        "meta_description": treatment.meta_description
        or f"Everything about {treatment.name} in Roorkee: symptoms, process, estimated cost, and verified clinics offering it.",
        "schema_jsonld": schema.to_json_ld(
            schema.breadcrumb_list_schema(request, crumbs),
            schema.faq_page_schema(faqs),
            schema.item_list_schema(request, clinics),
        ),
    }
    return render(request, "clinics/treatment_detail.html", context)


def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug, is_active=True)
    clinics = (
        problem.clinics.filter(is_active=True)
        .select_related("city", "locality")
        .prefetch_related("verification_records")
    )
    faqs = ClinicFAQ.objects.filter(problem=problem, clinic__isnull=True)
    suggested_treatments = problem.suggested_treatment_categories.filter(is_active=True)
    related_posts = related_blog_posts_for_problem(problem)
    city = clinics[0].city if clinics else None
    crumbs = problem_breadcrumbs(problem, city=city)

    track_pageview(request, PageView.PageType.PROBLEM, page_slug=problem.slug, problem=problem, city=city)

    context = {
        "problem": problem,
        "clinics": clinics,
        "faqs": faqs,
        "suggested_treatments": suggested_treatments,
        "related_posts": related_posts,
        "problem_crumbs": crumbs,
        "page_source": "problem",
        "page_slug": problem.slug,
        "meta_title": problem.meta_title or f"{problem.name} in Roorkee — Causes & When to See a Dentist | BestDentistIn",
        "meta_description": problem.meta_description
        or f"Experiencing {problem.name.lower()} in Roorkee? Learn possible causes, when to seek urgent care, and find nearby dentists.",
        "schema_jsonld": schema.to_json_ld(
            schema.breadcrumb_list_schema(request, crumbs),
            schema.faq_page_schema(faqs),
            schema.item_list_schema(request, clinics),
        ),
    }
    return render(request, "clinics/problem_detail.html", context)
