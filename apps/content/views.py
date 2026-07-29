from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from apps.analytics.models import PageView
from apps.analytics.utils import track_pageview
from apps.seo import schema
from apps.seo.breadcrumbs import blog_detail_breadcrumbs, blog_list_breadcrumbs
from apps.seo.linking import related_pages_for_blog_post

from .models import BlogCategory, BlogPost


def blog_list(request):
    posts_qs = BlogPost.objects.filter(is_published=True).select_related("category")

    category_slug = request.GET.get("category")
    if category_slug:
        posts_qs = posts_qs.filter(category__slug=category_slug)

    paginator = Paginator(posts_qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    crumbs = blog_list_breadcrumbs()

    track_pageview(request, PageView.PageType.BLOG, page_slug=category_slug or "")

    context = {
        "page_obj": page_obj,
        "categories": BlogCategory.objects.all(),
        "active_category": category_slug,
        "blog_crumbs": crumbs,
        "meta_title": "Dental Health Blog | BestDentistIn",
        "meta_description": "Tips and guides on oral hygiene, tooth pain, root canals, braces, and kids' dentistry.",
        "schema_jsonld": schema.to_json_ld(schema.breadcrumb_list_schema(request, crumbs)),
    }
    return render(request, "content/blog_list.html", context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost.objects.select_related("category"), slug=slug, is_published=True)
    related_posts = (
        BlogPost.objects.filter(category=post.category, is_published=True)
        .exclude(id=post.id)[:3]
    )
    related_treatments, related_problems = related_pages_for_blog_post(post)
    crumbs = blog_detail_breadcrumbs(post)

    # Surface a few clinics relevant to the post's topic so the article has a real
    # WhatsApp/Call CTA, not just an outbound link — this is what makes a "blog CTA
    # click" a genuine Lead (page_source=blog) rather than just a page view.
    cta_clinics = []
    cta_treatment = related_treatments[0] if related_treatments else None
    if cta_treatment:
        cta_clinics = cta_treatment.clinics.filter(is_active=True).select_related("locality", "city")[:3]

    track_pageview(request, PageView.PageType.BLOG, page_slug=post.slug)

    context = {
        "post": post,
        "related_posts": related_posts,
        "related_treatments": related_treatments,
        "related_problems": related_problems,
        "cta_treatment": cta_treatment,
        "cta_clinics": cta_clinics,
        "blog_crumbs": crumbs,
        "page_source": "blog",
        "page_slug": post.slug,
        "meta_title": post.meta_title or f"{post.title} | BestDentistIn Blog",
        "meta_description": post.meta_description or post.excerpt,
        "schema_jsonld": schema.to_json_ld(
            schema.breadcrumb_list_schema(request, crumbs),
            schema.article_schema(request, post),
        ),
    }
    return render(request, "content/blog_detail.html", context)
