from django.urls import path

from . import views

app_name = "code_to_bpmn"

urlpatterns = [
    path("", views.index, name="index"),
]
