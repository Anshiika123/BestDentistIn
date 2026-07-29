from django.conf import settings
from django.db import models


class ClinicUser(models.Model):
    """
    Links a Django auth User to a Clinic for the clinic-facing SaaS dashboard
    (apps.portal). BestDentistIn staff use plain Django admin accounts
    (User.is_staff) and never need a ClinicUser row.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Clinic Owner"
        STAFF = "staff", "Clinic Staff"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="clinic_profile", on_delete=models.CASCADE)
    clinic = models.ForeignKey("clinics.Clinic", related_name="portal_users", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)
    phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["clinic", "role"]

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_role_display()} at {self.clinic.name})"

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER
