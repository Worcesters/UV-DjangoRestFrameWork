from django.urls import path

from .views import CodeToBpmnIndexView

app_name = "code_to_bpmn"

urlpatterns = [
    path("", CodeToBpmnIndexView.as_view(), name="index"),
]
