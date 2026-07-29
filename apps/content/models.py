from django.db import models
from django.urls import reverse
from django.utils import timezone


class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    # Drives the internal-linking engine: treatment/problem pages surface posts
    # from categories linked here, and posts surface links back to these pages.
    treatments = models.ManyToManyField(
        "clinics.Treatment", blank=True, related_name="blog_categories"
    )
    problems = models.ManyToManyField(
        "clinics.Problem", blank=True, related_name="blog_categories"
    )

    class Meta:
        verbose_name_plural = "Blog categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True)
    category = models.ForeignKey(BlogCategory, related_name="posts", on_delete=models.SET_NULL, null=True)

    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField(help_text="Placeholder content in Phase 1; supports basic HTML/markdown-like text.")
    cover_image = models.ImageField(upload_to="blog/covers/", blank=True, null=True)

    author_name = models.CharField(max_length=120, default="BestDentistIn Team")
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:blog_detail", kwargs={"slug": self.slug})
