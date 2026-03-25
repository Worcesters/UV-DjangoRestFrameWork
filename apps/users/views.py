from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import UserForm
from .models import User
from . import services


# -----------------------------------------------------------------------------
# Accueil & pages statiques
# -----------------------------------------------------------------------------


class HomeView(TemplateView):
    """Landing (particles, hero, features)."""

    template_name = "index.html"


class PublicProfileView(TemplateView):
    """Profil public type CV interactif."""

    template_name = "public_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(services.get_public_profile_context())
        return context


# -----------------------------------------------------------------------------
# Documents Markdown (fichiers dans MARKDOWN_DOCS_DIR)
# -----------------------------------------------------------------------------


class DocumentsListView(TemplateView):
    """Page liste des fichiers .md du dossier configuré."""

    template_name = "documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = services.markdown_document_service.list_ordered()
        return context


class DocumentDetailView(View):
    """Affichage d'un fichier Markdown rendu en HTML."""

    def get(self, request, slug, *args, **kwargs):
        doc = services.markdown_document_service.get_by_slug(slug)
        if doc is None:
            raise Http404("Document introuvable.")
        return render(
            request,
            "users/document_detail.html",
            {
                "doc": doc,
                "html_content": services.markdown_document_service.render_html(doc.content),
            },
        )


# -----------------------------------------------------------------------------
# Hub outils de génération
# -----------------------------------------------------------------------------


class GenerationToolsView(View):
    """Hub multi-outils (GET/POST même rendu, contexte dans le service)."""

    template_name = "generation_tools.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, services.build_generation_tools_context(request))

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, services.build_generation_tools_context(request))


# -----------------------------------------------------------------------------
# API & utilitaires
# -----------------------------------------------------------------------------


class ApiPlantumlPreviewUrlView(View):
    """POST : retourne l’URL de preview PlantUML pour le texte donné."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        uml_text = request.POST.get("uml_text", "").strip()
        if not uml_text:
            return JsonResponse({"error": "uml_text required"}, status=400)
        try:
            from apps.code_converter_uml.services import build_plantuml_preview_url

            preview_url = build_plantuml_preview_url(uml_text)
            return JsonResponse({"preview_url": preview_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ApiHelloView(APIView):
    """GET : fragment HTMX ou JSON DRF."""

    def get(self, request, *args, **kwargs):
        if request.headers.get("HX-Request"):
            return render(request, "partials/hello_response.html")
        return Response({"message": "Hello from DRF JSON"})


# -----------------------------------------------------------------------------
# Profil connecté
# -----------------------------------------------------------------------------


class ProfileView(LoginRequiredMixin, TemplateView):
    """Profil utilisateur connecté."""

    login_url = reverse_lazy("users:login")
    template_name = "users/profile.html"


# -----------------------------------------------------------------------------
# Auth : inscription, connexion, liste utilisateurs (HTMX)
# -----------------------------------------------------------------------------


class SignupView(View):
    """Inscription avec `UserForm` (page complète ou fragment HTMX)."""

    form_class = UserForm
    template_name = "users/signup.html"
    partial_template_name = "partials/user_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = "/"
                return response
            return redirect("users:index")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        users = User.objects.all().order_by("-date_joined")
        users_display = services.build_users_display(users)
        form = self.form_class()
        context = {"users_display": users_display, "form": form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        users = User.objects.all().order_by("-date_joined")
        users_display = services.build_users_display(users)
        form = self.form_class(request.POST)
        if form.is_valid():
            success, _ = services.try_register_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                societe=form.cleaned_data.get("societe", ""),
            )
            if success:
                response = render(
                    request,
                    self.partial_template_name,
                    {
                        "success": True,
                        "active_tab": "signup",
                        "form": self.form_class(),
                        "errors": {},
                    },
                )
                response["HX-Trigger"] = "refreshList"
                return response
            form.add_error("email", "Cet email est déjà utilisé.")
        return render(
            request,
            self.partial_template_name,
            {
                "form": form,
                "active_tab": "signup",
                "users_display": users_display,
                "errors": {},
            },
        )


class LoginView(View):
    """Connexion (fragment HTMX + headers de redirection)."""

    partial_template_name = "partials/user_form.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.headers.get("HX-Request"):
                response = render(
                    request,
                    self.partial_template_name,
                    {"active_tab": "login", "form": UserForm()},
                )
                response["HX-Redirect"] = "/"
                return response
            return redirect("index")
        users = User.objects.all().order_by("-date_joined")
        users_display = services.build_users_display(users)
        form = UserForm()
        context = {"users_display": users_display, "form": form, "active_tab": "login"}
        return render(request, "users/signup.html", context)

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = services.authenticate_user(email=email, password=password)
        if user is not None:
            login(request, user)
            response = render(
                request,
                self.partial_template_name,
                {
                    "login_success": True,
                    "active_tab": "login",
                    "errors": {},
                    "form": UserForm(),
                },
            )
            response["HX-Redirect"] = "/"
            return response
        return render(
            request,
            self.partial_template_name,
            {
                "errors": {"login": "Identifiants invalides."},
                "active_tab": "login",
                "form": UserForm(),
                "login_email": email,
            },
        )


class LogoutRedirectView(DjangoLogoutView):
    """Déconnexion (POST) puis redirection vers l’accueil."""

    next_page = reverse_lazy("users:index")


def page_not_found(request, exception=None):
    """Page 404 personnalisée (handler404 en prod, ou route catch-all en DEBUG)."""
    return render(request, "404.html", status=404)


def catch_all_404(request, catchall):
    """DEBUG uniquement : toute URL non couverte par les routes précédentes → même 404 que en production."""
    return page_not_found(request, None)


class UserListPartialView(ListView):
    """Fragment : tableau des utilisateurs (pseudos)."""

    model = User
    template_name = "partials/user_table.html"
    ordering = ["-date_joined"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users_display"] = services.build_users_display(context["object_list"])
        return context