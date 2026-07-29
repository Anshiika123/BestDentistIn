from django.urls import path

from . import views

app_name = "clinics"

urlpatterns = [
    path("clinic/<slug:slug>/", views.clinic_detail, name="clinic_detail"),
    path("treatments/<slug:slug>/", views.treatment_detail, name="treatment_detail"),
    path("problems/<slug:slug>/", views.problem_detail, name="problem_detail"),
]
