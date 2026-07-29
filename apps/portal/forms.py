from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.clinics.models import Clinic
from apps.leads.models import Lead

INPUT_CLASSES = "w-full rounded-lg border-gray-300 text-sm focus:ring-2 focus:ring-brand-500"


class PortalAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = INPUT_CLASSES
        self.fields["password"].widget.attrs["class"] = INPUT_CLASSES


class LeadUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["status", "follow_up_type", "follow_up_date", "missed_reason", "assigned_to"]
        widgets = {
            "follow_up_date": forms.DateInput(attrs={"type": "date"}),
            "missed_reason": forms.TextInput(attrs={"placeholder": "e.g. Patient did not answer"}),
        }

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic is not None:
            self.fields["assigned_to"].queryset = clinic.portal_users.filter(is_active=True)
        for name, field in self.fields.items():
            css = "rounded-lg border-gray-300 text-sm w-full"
            field.widget.attrs.setdefault("class", css)


class LeadNoteForm(forms.Form):
    note = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 2, "class": "rounded-lg border-gray-300 text-sm w-full", "placeholder": "Add a note..."}
        )
    )


class ClinicSettingsForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ["phone_number", "whatsapp_number", "timings", "consultation_fee", "about"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "rounded-lg border-gray-300 text-sm w-full")
