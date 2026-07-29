from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("leads/", views.leads_list, name="leads_list"),
    path("clinics/", views.clinics_list, name="clinics_list"),
    path("pages/", views.pages_performance, name="pages_performance"),
    path("content/", views.content_performance, name="content_performance"),
]
