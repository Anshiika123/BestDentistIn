from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("go/whatsapp/<slug:clinic_slug>/", views.track_whatsapp, name="track_whatsapp"),
    path("go/call/<slug:clinic_slug>/", views.track_call, name="track_call"),
]
