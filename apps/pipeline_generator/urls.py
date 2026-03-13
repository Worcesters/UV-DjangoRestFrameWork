from django.urls import path

from .views import branches_api, index

app_name = "pipeline_generator"

urlpatterns = [
    path("", index, name="index"),
    path("api/branches/", branches_api, name="branches_api"),
]
