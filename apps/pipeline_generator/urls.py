from django.urls import path

from .views import BranchesApiView, PipelineGeneratorIndexView

app_name = "pipeline_generator"

urlpatterns = [
    path("", PipelineGeneratorIndexView.as_view(), name="index"),
    path("api/branches/", BranchesApiView.as_view(), name="branches_api"),
]
