from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_city(apps, schema_editor):
    Treatment = apps.get_model("clinics", "Treatment")
    Problem = apps.get_model("clinics", "Problem")
    City = apps.get_model("locations", "City")

    primary_city_slug = getattr(settings, "PRIMARY_CITY_SLUG", "roorkee")
    city = City.objects.filter(slug=primary_city_slug).first() or City.objects.first()
    if not city:
        return  # No cities seeded yet — nothing to backfill.

    Treatment.objects.filter(city__isnull=True).update(city=city)
    Problem.objects.filter(city__isnull=True).update(city=city)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0001_initial"),
        ("clinics", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="treatment",
            name="city",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="treatments",
                to="locations.city",
            ),
        ),
        migrations.AddField(
            model_name="problem",
            name="city",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="problems",
                to="locations.city",
            ),
        ),
        migrations.RunPython(backfill_city, noop_reverse),
        migrations.AlterField(
            model_name="treatment",
            name="city",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="treatments", to="locations.city"
            ),
        ),
        migrations.AlterField(
            model_name="problem",
            name="city",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="problems", to="locations.city"
            ),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="name",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="slug",
            field=models.SlugField(help_text="e.g. root-canal", max_length=180),
        ),
        migrations.AlterField(
            model_name="problem",
            name="name",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="problem",
            name="slug",
            field=models.SlugField(help_text="e.g. tooth-pain", max_length=180),
        ),
        migrations.AlterUniqueTogether(
            name="treatment",
            unique_together={("city", "slug")},
        ),
        migrations.AlterUniqueTogether(
            name="problem",
            unique_together={("city", "slug")},
        ),
    ]
