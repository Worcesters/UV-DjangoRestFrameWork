from django.urls import path

from .views import GameWorldView

app_name = "experience"

urlpatterns = [
    path("explore/", GameWorldView.as_view(), name="explore"),
]
