from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("login/", views.PortalLoginView.as_view(), name="login"),
    path("logout/", views.portal_logout, name="logout"),
    path("", views.overview, name="overview"),
    path("leads/", views.leads_list, name="leads_list"),
    path("leads/<int:lead_id>/", views.lead_detail, name="lead_detail"),
    path("analytics/", views.analytics, name="analytics"),
    path("reminders/", views.reminders, name="reminders"),
    path("settings/", views.settings_view, name="settings"),
]
