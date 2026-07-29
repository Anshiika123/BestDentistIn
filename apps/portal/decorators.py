from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from apps.accounts.models import ClinicUser


def clinic_login_required(view_func):
    """
    Requires an authenticated user with an active ClinicUser profile, and
    attaches it to the request as `request.clinic_user` for the view to use.
    Django staff/superusers manage clinics through /admin/, not /portal/, so
    they're deliberately not given a bypass here.
    """

    @wraps(view_func)
    @login_required(login_url="portal:login")
    def wrapper(request, *args, **kwargs):
        clinic_user = ClinicUser.objects.filter(user=request.user, is_active=True).select_related("clinic").first()
        if not clinic_user:
            from django.contrib.auth import logout
            from django.contrib import messages

            logout(request)
            messages.error(request, "This account isn't linked to an active clinic. Contact BestDentistIn support.")
            return redirect("portal:login")
        request.clinic_user = clinic_user
        return view_func(request, *args, **kwargs)

    return wrapper


def owner_required(view_func):
    """Stack after clinic_login_required — restricts a view to the clinic owner role."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from django.contrib import messages

        if not request.clinic_user.is_owner:
            messages.error(request, "Only the clinic owner can access this page.")
            return redirect("portal:overview")
        return view_func(request, *args, **kwargs)

    return wrapper
