from django.urls import path

from .views import index

app_name = "codegenerator"

urlpatterns = [
    path("", index, name="index"),
]
