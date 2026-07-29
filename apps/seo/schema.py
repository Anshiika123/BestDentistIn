"""
JSON-LD schema.org helpers. Views build one or more schema dicts and pass them
to `to_json_ld()`, which combines them into a single <script type="application/ld+json">
payload (using @graph when there's more than one) for base.html to render.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe


def breadcrumb_list_schema(request, crumbs):
    """crumbs: list of (label, url|None) tuples, in order, url=None means current page."""
    items = []
    for position, (label, url) in enumerate(crumbs, start=1):
        item_url = url or request.path
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": label,
                "item": request.build_absolute_uri(item_url),
            }
        )
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def faq_page_schema(faqs):
    faqs = list(faqs)
    if not faqs:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }


def local_business_schema(request, clinic):
    data = {
        "@context": "https://schema.org",
        "@type": "Dentist",
        "name": clinic.name,
        "url": request.build_absolute_uri(clinic.get_absolute_url()),
        "telephone": clinic.phone_number,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": clinic.address,
            "addressLocality": clinic.locality.name,
            "addressRegion": clinic.city.state,
            "addressCountry": "IN",
        },
    }
    if clinic.timings:
        data["openingHours"] = clinic.timings
    if clinic.latitude is not None and clinic.longitude is not None:
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(clinic.latitude),
            "longitude": float(clinic.longitude),
        }
    return data


def article_schema(request, post):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.title,
        "author": {"@type": "Person", "name": post.author_name},
        "datePublished": post.published_at.isoformat(),
        "dateModified": post.updated_at.isoformat(),
        "mainEntityOfPage": request.build_absolute_uri(post.get_absolute_url()),
    }


def item_list_schema(request, items, url_attr="get_absolute_url", limit=10):
    elements = []
    for position, item in enumerate(list(items)[:limit], start=1):
        url = getattr(item, url_attr)
        url = url() if callable(url) else url
        elements.append(
            {"@type": "ListItem", "position": position, "url": request.build_absolute_uri(url)}
        )
    if not elements:
        return None
    return {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": elements}


def to_json_ld(*schemas):
    """Combine schema dicts (dropping any None entries) into one safe <script> payload."""
    valid = [s for s in schemas if s]
    if not valid:
        return ""
    if len(valid) == 1:
        payload = valid[0]
    else:
        payload = {
            "@context": "https://schema.org",
            "@graph": [{k: v for k, v in s.items() if k != "@context"} for s in valid],
        }
    raw = json.dumps(payload, cls=DjangoJSONEncoder)
    return mark_safe(raw.replace("</script>", "<\\/script>"))
