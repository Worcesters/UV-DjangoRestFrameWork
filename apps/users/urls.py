from django.urls import path

from .views import (
    ApiHelloView,
    ApiPlantumlPreviewUrlView,
    DocumentDetailView,
    DocumentsListView,
    GenerationToolsView,
    HomeView,
    LoginView,
    LogoutRedirectView,
    ProfileView,
    PublicProfileView,
    SignupView,
    UserListPartialView,
)

app_name = "users"

urlpatterns = [
    path("", HomeView.as_view(), name="index"),
    path("profil-public/", PublicProfileView.as_view(), name="public_profile"),
    path("outils-generation/", GenerationToolsView.as_view(), name="generation_tools"),
    path("documents/", DocumentsListView.as_view(), name="documents"),
    path("api/hello/", ApiHelloView.as_view(), name="api_hello"),
    path("api/plantuml-preview-url/", ApiPlantumlPreviewUrlView.as_view(), name="api_plantuml_preview_url"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("list-users/", UserListPartialView.as_view(), name="user_list"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutRedirectView.as_view(), name="logout"),
    path("docs/<slug:slug>/", DocumentDetailView.as_view(), name="document_detail"),
]
