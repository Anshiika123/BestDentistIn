from django.http import HttpResponse


def robots_txt(request):
    host = request.build_absolute_uri("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /leads/go/",
        f"Sitemap: {host.rstrip('/')}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
