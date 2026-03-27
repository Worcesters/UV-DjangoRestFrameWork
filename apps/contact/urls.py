from django.urls import path

from .views import ContactIndexView, ContactSocieteExtraView

app_name = "contact"

urlpatterns = [
    path("", ContactIndexView.as_view(), name="index"),
    path("societe-extra/", ContactSocieteExtraView.as_view(), name="societe_extra"),
]
