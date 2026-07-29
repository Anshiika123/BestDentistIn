from django.urls import path

from . import views

app_name = "locations"

urlpatterns = [
    path("dentist-in-<slug:rest>/", views.city_or_locality, name="city_or_locality"),
]
