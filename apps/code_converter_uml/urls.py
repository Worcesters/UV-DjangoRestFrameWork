from django.urls import path

from .views import CodeConverterUmlIndexView

app_name = "code_converter_uml"

urlpatterns = [
    path("", CodeConverterUmlIndexView.as_view(), name="index"),
]
