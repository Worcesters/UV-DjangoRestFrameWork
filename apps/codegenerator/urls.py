from django.urls import path

from .views import CodeGeneratorIndexView

app_name = "codegenerator"

urlpatterns = [
    path("", CodeGeneratorIndexView.as_view(), name="index"),
]
