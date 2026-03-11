from django.urls import path

from .views import index

app_name = "code_converter_uml"

urlpatterns = [
    path("", index, name="index"),
]
