from django.urls import path

from . import views

app_name = "intake"

urlpatterns = [
    path("", views.intake_start, name="start"),
    path("<uuid:session_key>/", views.intake_results, name="results"),
]
