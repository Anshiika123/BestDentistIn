import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import ClinicUser
from apps.clinics.models import Clinic
from apps.leads.models import Lead

DEMO_PASSWORD = "clinic12345"


class Command(BaseCommand):
    help = (
        "Seed demo clinic portal accounts + synthetic leads so /portal/ has something to show. "
        "Run seed_roorkee first. Safe to re-run (idempotent on usernames)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--clinics", type=int, default=3, help="How many clinics to set up portal demo data for.")
        parser.add_argument("--leads-per-clinic", type=int, default=12)
        parser.add_argument("--seed", type=int, default=7)

    def handle(self, *args, **options):
        random.seed(options["seed"])
        clinics = list(Clinic.objects.filter(is_active=True)[: options["clinics"]])
        if not clinics:
            self.stdout.write(self.style.ERROR("No clinics found — run `manage.py seed_roorkee` first."))
            return

        for clinic in clinics:
            owner_username = f"{clinic.slug}-owner"[:150]
            owner_user, created = User.objects.get_or_create(
                username=owner_username,
                defaults={"email": f"{owner_username}@example.com"},
            )
            if created:
                owner_user.set_password(DEMO_PASSWORD)
                owner_user.save()
            owner, _ = ClinicUser.objects.update_or_create(
                user=owner_user, defaults={"clinic": clinic, "role": ClinicUser.Role.OWNER, "is_active": True}
            )

            staff_username = f"{clinic.slug}-staff"[:150]
            staff_user, created = User.objects.get_or_create(
                username=staff_username,
                defaults={"email": f"{staff_username}@example.com"},
            )
            if created:
                staff_user.set_password(DEMO_PASSWORD)
                staff_user.save()
            staff, _ = ClinicUser.objects.update_or_create(
                user=staff_user, defaults={"clinic": clinic, "role": ClinicUser.Role.STAFF, "is_active": True}
            )

            self._seed_leads(clinic, [owner, staff], options["leads_per_clinic"])

            self.stdout.write(f"{clinic.name}: login as '{owner_username}' / '{staff_username}', password '{DEMO_PASSWORD}'")

        self.stdout.write(self.style.SUCCESS(f"Portal demo data ready for {len(clinics)} clinic(s)."))

    def _seed_leads(self, clinic, clinic_users, count):
        treatments = list(clinic.treatments.all())
        problems = list(clinic.problems.all())
        page_sources = [c[0] for c in Lead.PageSource.choices if c[0] != Lead.PageSource.INTAKE]
        statuses = [c[0] for c in Lead.Status.choices]

        for _ in range(count):
            created_at = timezone.now() - timedelta(hours=random.randint(0, 240))
            status = random.choice(statuses)
            follow_up_type = Lead.FollowUp.NONE
            follow_up_date = None
            if status in (Lead.Status.NEW, Lead.Status.CONTACTED):
                follow_up_type = random.choice(
                    [Lead.FollowUp.TODAY, Lead.FollowUp.TOMORROW, Lead.FollowUp.LATER, Lead.FollowUp.NONE]
                )
                if follow_up_type == Lead.FollowUp.TODAY:
                    follow_up_date = timezone.localdate()
                elif follow_up_type == Lead.FollowUp.TOMORROW:
                    follow_up_date = timezone.localdate() + timedelta(days=1)
                elif follow_up_type == Lead.FollowUp.LATER:
                    follow_up_date = timezone.localdate() + timedelta(days=random.randint(2, 7))

            lead = Lead.objects.create(
                clinic=clinic,
                city=clinic.city,
                locality=clinic.locality,
                cta_type=random.choice([Lead.CtaType.WHATSAPP, Lead.CtaType.CALL]),
                page_source=random.choice(page_sources),
                treatment=random.choice(treatments) if treatments and random.random() < 0.6 else None,
                problem=random.choice(problems) if problems and random.random() < 0.4 else None,
                status=status,
                follow_up_type=follow_up_type,
                follow_up_date=follow_up_date,
                assigned_to=random.choice(clinic_users) if random.random() < 0.5 else None,
                missed_reason="Patient did not answer" if status == Lead.Status.NOT_REACHABLE else "",
            )
            # created_at has auto_now_add — backdate it directly for realistic demo data.
            Lead.objects.filter(id=lead.id).update(created_at=created_at)
