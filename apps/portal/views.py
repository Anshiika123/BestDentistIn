from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.leads.models import Lead, LeadActivityLog, LeadNote

from .decorators import clinic_login_required, owner_required
from .forms import ClinicSettingsForm, LeadNoteForm, LeadUpdateForm, PortalAuthenticationForm


class PortalLoginView(auth_views.LoginView):
    template_name = "portal/login.html"
    authentication_form = PortalAuthenticationForm
    redirect_authenticated_user = True
    next_page = "/portal/"

    def get_success_url(self):
        return self.get_redirect_url() or "/portal/"


@login_required(login_url="portal:login")
def portal_logout(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect("portal:login")


def _log_activity(lead, clinic_user, action, from_value="", to_value=""):
    LeadActivityLog.objects.create(
        lead=lead, actor=clinic_user, action=action, from_value=str(from_value), to_value=str(to_value)
    )


def _can_edit(lead, clinic_user):
    if clinic_user.is_owner:
        return True
    return lead.assigned_to_id in (None, clinic_user.id)


@clinic_login_required
def overview(request):
    clinic = request.clinic_user.clinic
    leads = Lead.objects.filter(clinic=clinic)

    today = timezone.localdate()
    stale_cutoff = timezone.now() - timedelta(hours=24)

    context = {
        "clinic": clinic,
        "total_leads": leads.count(),
        "new_leads": leads.filter(status=Lead.Status.NEW).count(),
        "whatsapp_leads": leads.filter(cta_type=Lead.CtaType.WHATSAPP).count(),
        "call_leads": leads.filter(cta_type=Lead.CtaType.CALL).count(),
        "follow_up_today": leads.filter(follow_up_date=today).count(),
        "missed_or_stale": leads.filter(status=Lead.Status.NEW, created_at__lt=stale_cutoff).count()
        + leads.filter(status=Lead.Status.MISSED).count(),
        "status_counts": leads.values("status").annotate(total=Count("id")).order_by("-total"),
        "recent_leads": leads.select_related("treatment", "problem")[:10],
    }
    return render(request, "portal/overview.html", context)


@clinic_login_required
def leads_list(request):
    clinic = request.clinic_user.clinic
    leads = Lead.objects.filter(clinic=clinic).select_related("treatment", "problem", "assigned_to__user")

    status = request.GET.get("status")
    if status:
        leads = leads.filter(status=status)

    cta_type = request.GET.get("cta_type")
    if cta_type:
        leads = leads.filter(cta_type=cta_type)

    mine_only = request.GET.get("mine") == "1"
    if mine_only:
        leads = leads.filter(assigned_to=request.clinic_user)

    context = {
        "leads": leads[:200],
        "status_choices": Lead.Status.choices,
        "cta_choices": Lead.CtaType.choices,
        "mine_only": mine_only,
    }
    return render(request, "portal/leads_list.html", context)


@clinic_login_required
def lead_detail(request, lead_id):
    clinic_user = request.clinic_user
    lead = get_object_or_404(Lead.objects.select_related("treatment", "problem", "assigned_to__user"), id=lead_id, clinic=clinic_user.clinic)

    can_edit = _can_edit(lead, clinic_user)

    if request.method == "POST" and can_edit:
        if "add_note" in request.POST:
            note_form = LeadNoteForm(request.POST)
            update_form = LeadUpdateForm(instance=lead, clinic=clinic_user.clinic)
            if note_form.is_valid():
                LeadNote.objects.create(lead=lead, author=clinic_user, note=note_form.cleaned_data["note"])
                _log_activity(lead, clinic_user, LeadActivityLog.Action.NOTE_ADDED)
                messages.success(request, "Note added.")
                return redirect("portal:lead_detail", lead_id=lead.id)
        else:
            note_form = LeadNoteForm()
            old_status, old_follow_up, old_assignee = lead.status, lead.follow_up_type, lead.assigned_to_id
            update_form = LeadUpdateForm(request.POST, instance=lead, clinic=clinic_user.clinic)
            if update_form.is_valid():
                updated = update_form.save(commit=False)
                if old_status != updated.status and updated.status in (Lead.Status.CONTACTED, Lead.Status.SCHEDULED, Lead.Status.VISITED):
                    updated.last_contacted_at = timezone.now()
                updated.save()

                if old_status != updated.status:
                    _log_activity(lead, clinic_user, LeadActivityLog.Action.STATUS_CHANGED, old_status, updated.status)
                if old_follow_up != updated.follow_up_type:
                    _log_activity(lead, clinic_user, LeadActivityLog.Action.FOLLOW_UP_SET, old_follow_up, updated.follow_up_type)
                if old_assignee != updated.assigned_to_id:
                    _log_activity(lead, clinic_user, LeadActivityLog.Action.ASSIGNED, old_assignee or "-", updated.assigned_to_id or "-")

                messages.success(request, "Lead updated.")
                return redirect("portal:lead_detail", lead_id=lead.id)
    else:
        update_form = LeadUpdateForm(instance=lead, clinic=clinic_user.clinic)
        note_form = LeadNoteForm()

    context = {
        "lead": lead,
        "update_form": update_form,
        "note_form": note_form,
        "can_edit": can_edit,
        "notes": lead.notes.select_related("author__user"),
        "activity_log": lead.activity_log.select_related("actor__user"),
    }
    return render(request, "portal/lead_detail.html", context)


@clinic_login_required
def analytics(request):
    clinic = request.clinic_user.clinic
    leads = Lead.objects.filter(clinic=clinic)

    context = {
        "total_leads": leads.count(),
        "whatsapp_leads": leads.filter(cta_type=Lead.CtaType.WHATSAPP).count(),
        "call_leads": leads.filter(cta_type=Lead.CtaType.CALL).count(),
        "by_page_source": leads.values("page_source").annotate(total=Count("id")).order_by("-total"),
        "by_treatment": leads.exclude(treatment__isnull=True).values("treatment__name").annotate(total=Count("id")).order_by("-total")[:10],
        "by_problem": leads.exclude(problem__isnull=True).values("problem__name").annotate(total=Count("id")).order_by("-total")[:10],
        "by_locality": leads.exclude(locality__isnull=True).values("locality__name").annotate(total=Count("id")).order_by("-total")[:10],
        "status_counts": leads.values("status").annotate(total=Count("id")).order_by("-total"),
        "recent_leads": leads.select_related("treatment", "problem")[:15],
    }
    return render(request, "portal/analytics.html", context)


@clinic_login_required
def reminders(request):
    clinic = request.clinic_user.clinic
    today = timezone.localdate()
    leads = Lead.objects.filter(clinic=clinic).exclude(status__in=[Lead.Status.CLOSED, Lead.Status.VISITED])

    context = {
        "overdue": leads.filter(follow_up_date__lt=today).exclude(follow_up_type=Lead.FollowUp.NONE),
        "today": leads.filter(follow_up_date=today),
        "upcoming": leads.filter(follow_up_date__gt=today),
        "missed_no_response": leads.filter(
            status=Lead.Status.NEW, created_at__lt=timezone.now() - timedelta(hours=24)
        ),
    }
    return render(request, "portal/reminders.html", context)


@clinic_login_required
@owner_required
def settings_view(request):
    clinic = request.clinic_user.clinic

    if request.method == "POST":
        form = ClinicSettingsForm(request.POST, instance=clinic)
        if form.is_valid():
            form.save()
            messages.success(request, "Clinic settings updated.")
            return redirect("portal:settings")
    else:
        form = ClinicSettingsForm(instance=clinic)

    context = {
        "clinic": clinic,
        "form": form,
        "team": clinic.portal_users.select_related("user"),
    }
    return render(request, "portal/settings.html", context)
