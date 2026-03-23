import json

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import PipelineConfigForm
from .services import PipelineGenerationError, generate_pipeline_config
from .services.git_service import GitBranchFetchError, fetch_remote_branches


@method_decorator(xframe_options_sameorigin, name="dispatch")
class PipelineGeneratorIndexView(View):
    """Formulaire de génération de configuration pipeline (Git/Jenkins)."""

    template_name = "pipeline_generator/page.html"
    form_class = PipelineConfigForm

    def get(self, request, *args, **kwargs):
        context = {
            "form": self.form_class(),
            "generated_config": "",
            "error_message": "",
            "containers_initial_json": "[]",
            "form_action": reverse("pipeline_generator:index"),
        }
        self._sanitize_containers_json(context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {
            "form": form,
            "generated_config": "",
            "error_message": "",
            "containers_initial_json": form.data.get("containers_json", "[]"),
            "form_action": reverse("pipeline_generator:index"),
        }
        if form.is_valid():
            data = {
                "project_name": form.cleaned_data["project_name"],
                "deploy_target": form.cleaned_data["deploy_target"],
                "use_containers": form.cleaned_data["use_containers"],
                "command_shell": form.cleaned_data["command_shell"],
                "use_ssh": form.cleaned_data["use_ssh"],
                "repo_url": form.cleaned_data.get("repo_url", ""),
                "deploy_branch": form.cleaned_data.get("deploy_branch", "main"),
                "env_variables": form.cleaned_data.get("env_variables", ""),
                "ssh_host": form.cleaned_data.get("ssh_host", ""),
                "ssh_user": form.cleaned_data.get("ssh_user", ""),
                "ssh_port": form.cleaned_data.get("ssh_port", "22"),
                "ssh_key_variable": form.cleaned_data.get("ssh_key_variable", "SSH_PRIVATE_KEY"),
                "pre_deploy_commands": form.cleaned_data.get("pre_deploy_commands", ""),
                "deploy_commands": form.cleaned_data.get("deploy_commands", ""),
                "post_deploy_commands": form.cleaned_data.get("post_deploy_commands", ""),
                "containers_json": form.cleaned_data.get("containers_json", "[]"),
            }
            try:
                context["generated_config"] = generate_pipeline_config(data)
            except PipelineGenerationError as exc:
                context["error_message"] = str(exc)
            except Exception as exc:  # pragma: no cover
                context["error_message"] = f"Erreur interne de generation: {exc}"
        self._sanitize_containers_json(context)
        return render(request, self.template_name, context)

    @staticmethod
    def _sanitize_containers_json(context: dict) -> None:
        try:
            json.loads(context["containers_initial_json"])
        except json.JSONDecodeError:
            context["containers_initial_json"] = "[]"


class BranchesApiView(View):
    """GET : branches distantes pour un dépôt Git (JSON)."""

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        repo_url = request.GET.get("repo_url", "").strip()
        if not repo_url:
            return JsonResponse({"error": "repo_url est requis."}, status=400)
        try:
            branches = fetch_remote_branches(repo_url)
        except GitBranchFetchError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        except Exception as exc:  # pragma: no cover
            return JsonResponse({"error": f"Erreur interne: {exc}"}, status=500)
        return JsonResponse({"branches": branches})
