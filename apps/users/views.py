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


class ApiUmlDispatchAnalyzeView(View):
    """POST : analyse un PlantUML et retourne les groupes proposés (JSON).

    Réponse : ``{"groups": [{"target", "folder", "members", "count"}],
    "unlinked": [...], "total_classes": int}``. Sert à l'aperçu éditable
    de l'arborescence côté client, sans upload de fichier.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        from apps.uml_dispatcher.services import DispatchError, build_dispatch_plan

        uml_text = request.POST.get("plantuml_text", "").strip()
        if not uml_text:
            return JsonResponse({"error": "plantuml_text requis"}, status=400)
        try:
            plan = build_dispatch_plan(uml_text)
        except DispatchError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001 - message d'erreur générique côté UI
            return JsonResponse({"error": f"Erreur interne: {exc}"}, status=500)
        return JsonResponse(
            {
                "groups": [
                    {
                        "target": g.target,
                        "folder": g.folder,
                        "members": list(g.members),
                        "count": len(g.members),
                    }
                    for g in plan.groups
                ],
                "unlinked": list(plan.unlinked),
                "total_classes": len(plan.class_names),
            }
        )


class UmlDispatchGenerateView(View):
    """POST : construit et renvoie le ZIP réorganisé (téléchargement).

    En cas d'erreur (formulaire, ZIP invalide), ré-affiche le hub avec le
    message d'erreur au lieu de forcer un téléchargement.
    """

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        from apps.uml_dispatcher.forms import UmlDispatchForm

        form = UmlDispatchForm(request.POST, request.FILES)
        if not form.is_valid():
            message = "; ".join(
                f"{field}: {', '.join(errs)}" for field, errs in form.errors.items()
            )
            return self._render_error(request, form, message or "Formulaire invalide.")
        return self._build_or_error(request, form)

    def _build_or_error(self, request, form):
        from apps.uml_dispatcher.services import (
            DispatchError,
            ZipDispatchError,
            build_dispatch_plan,
            build_placement,
            build_reorganized_zip,
        )

        try:
            plan = build_dispatch_plan(form.cleaned_data["plantuml_text"])
            overrides = self._parse_overrides(form.cleaned_data.get("folder_map", ""))
            placement = build_placement(plan, overrides)
            zip_bytes = build_reorganized_zip(
                form.cleaned_data["archive"].read(), placement
            )
        except (DispatchError, ZipDispatchError) as exc:
            return self._render_error(request, form, str(exc))
        except Exception as exc:  # noqa: BLE001
            return self._render_error(request, form, f"Erreur interne: {exc}")

        response = HttpResponse(zip_bytes, content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="reorganise.zip"'
        response["Content-Length"] = str(len(zip_bytes))
        response["Cache-Control"] = "no-store"
        return response

    @staticmethod
    def _parse_overrides(raw: str) -> dict:
        import json

        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items()}

    @staticmethod
    def _render_error(request, form, message: str):
        """Erreur JSON pour le téléchargement via fetch (évite une page blanche)."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": message}, status=400)
        context = services.build_empty_generation_context("uml_dispatch")
        context["dispatch_form"] = form
        context["dispatch_error"] = message
        return render(request, "generation_tools.html", context)


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
        return redirect("users:index")

    def post(self, request, *args, **kwargs):
        return redirect("users:index")


class LoginView(View):
    """Connexion (fragment HTMX + headers de redirection)."""

    partial_template_name = "partials/user_form.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:index")
        return redirect("users:index")

    def post(self, request, *args, **kwargs):
        return redirect("users:index")


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