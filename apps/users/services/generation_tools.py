"""
Hub « Outils de génération » : contexte unique pour les includes par outil.

Chaque handler POST met à jour le même dictionnaire de contexte que l’ancienne vue monolithique.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from django.http import HttpRequest
from django.urls import reverse

from apps.code_converter_uml.forms import UmlUploadForm
from apps.code_converter_uml.services import (
    UmlGenerationError,
    build_plantuml_preview_url,
    generate_uml_from_upload,
)
from apps.code_to_bpmn.forms import BpmnUploadForm
from apps.code_to_bpmn.services import BpmnGenerationError, generate_bpmn_from_sources
from apps.codegenerator.forms import CodeGeneratorForm
from apps.codegenerator.services import CodeGenerationError, generate_code_from_plantuml
from apps.pipeline_generator.forms import PipelineConfigForm
from apps.pipeline_generator.services import PipelineGenerationError, generate_pipeline_config

# Même structure que l’historique (urls affichées dans les métadonnées outil)
GENERATION_TOOLS: List[Dict[str, Any]] = [
    {
        "id": "uml",
        "name": "Code to UML",
        "description": "Convertit du code en PlantUML.",
        "url": "/uml/",
        "bg_type": "uml",
        "bg_snippet": "class MyClass {\n  + method()\n  - attribute",
    },
    {
        "id": "codegen",
        "name": "UML to Code",
        "description": "Genere du code depuis PlantUML.",
        "url": "/codegenerator/",
        "bg_type": "codegen",
        "bg_snippet": "PlantUML\n→ Code",
    },
    {
        "id": "uml_preview",
        "name": "UML Builder",
        "description": "Visualise & crée un diagramme.",
        "url": "/uml/",
        "bg_type": "uml",
        "bg_snippet": "@startuml\nclass User\nUser -> Service: call()\n@enduml",
    },
    {
        "id": "pipeline",
        "name": "PipelineGenerator",
        "description": "Genere une pipeline Git/Jenkins avec options avancees.",
        "url": "/pipeline-generator/",
        "bg_type": "pipeline",
        "bg_snippet": "git\njenkins",
    },
    {
        "id": "bpmn",
        "name": "Code to BPMN (alpha)",
        "description": "Genere un diagramme BPMN 2.0 a partir du code.",
        "url": "/code-to-bpmn/",
        "bg_type": "bpmn",
        "bg_snippet": "<process>\n  <task/>",
    },
]

_TOOL_IDS = {t["id"] for t in GENERATION_TOOLS}


def resolve_active_tool(request: HttpRequest) -> str:
    raw = request.GET.get("tool", "uml")
    if raw not in _TOOL_IDS:
        return "uml"
    return raw


def active_tool_display_name(active_tool: str) -> str:
    return next((t["name"] for t in GENERATION_TOOLS if t["id"] == active_tool), "Code to UML")


def form_action_url(active_tool: str) -> str:
    return reverse("users:generation_tools") + "?tool=" + active_tool


def _empty_context(active_tool: str) -> Dict[str, Any]:
    """Contexte par défaut (GET ou avant traitement POST)."""
    return {
        "tools": GENERATION_TOOLS,
        "default_tool_url": "/uml/",
        "active_tool": active_tool,
        "active_tool_name": active_tool_display_name(active_tool),
        "form_action": form_action_url(active_tool),
        "uml_form": UmlUploadForm(),
        "uml_code": "",
        "preview_url": "",
        "parsed_files": [],
        "detected_language": "",
        "uml_error_message": "",
        "codegen_form": CodeGeneratorForm(),
        "codegen_generated_code": "",
        "codegen_error_message": "",
        "pipeline_form": PipelineConfigForm(),
        "pipeline_generated_config": "",
        "pipeline_error_message": "",
        "pipeline_containers_initial_json": "[]",
        "bpmn_form": BpmnUploadForm(),
        "bpmn_xml": "",
        "bpmn_parsed_files": [],
        "bpmn_detected_language": "",
        "bpmn_error_message": "",
        "bpmn_preview_url": "",
    }


def _post_uml(request: HttpRequest, context: Dict[str, Any]) -> None:
    form = UmlUploadForm(request.POST, request.FILES)
    context["uml_form"] = form
    if form.is_valid():
        try:
            uml_code, parsed_files, detected_language = generate_uml_from_upload(
                uploaded_sources=request.FILES.getlist("sources"),
                uploaded_archive=form.cleaned_data.get("archive"),
                selected_language=form.cleaned_data["language"],
            )
            context["uml_code"] = uml_code
            context["preview_url"] = build_plantuml_preview_url(uml_code)
            context["parsed_files"] = parsed_files
            context["detected_language"] = detected_language
        except UmlGenerationError as e:
            context["uml_error_message"] = str(e)
        except Exception as e:
            context["uml_error_message"] = f"Erreur interne: {e}"


def _post_uml_preview(request: HttpRequest, context: Dict[str, Any]) -> None:
    uml_text = request.POST.get("uml_text", "").strip()
    context["uml_code"] = uml_text
    if uml_text:
        try:
            context["preview_url"] = build_plantuml_preview_url(uml_text)
        except Exception as e:
            context["uml_error_message"] = f"Erreur lors de la génération de la preview: {e}"
    else:
        context["uml_error_message"] = "Merci de coller du PlantUML avant de prévisualiser."


def _post_codegen(request: HttpRequest, context: Dict[str, Any]) -> None:
    form = CodeGeneratorForm(request.POST)
    context["codegen_form"] = form
    if form.is_valid():
        try:
            context["codegen_generated_code"] = generate_code_from_plantuml(
                plantuml_text=form.cleaned_data["plantuml"],
                language=form.cleaned_data["language"],
            )
        except CodeGenerationError as e:
            context["codegen_error_message"] = str(e)
        except Exception as e:
            context["codegen_error_message"] = f"Erreur interne: {e}"


def _post_pipeline(request: HttpRequest, context: Dict[str, Any]) -> None:
    form = PipelineConfigForm(request.POST)
    context["pipeline_form"] = form
    context["pipeline_containers_initial_json"] = form.data.get("containers_json", "[]")
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
            context["pipeline_generated_config"] = generate_pipeline_config(data)
        except PipelineGenerationError as e:
            context["pipeline_error_message"] = str(e)
        except Exception as e:
            context["pipeline_error_message"] = f"Erreur interne: {e}"
    try:
        json.loads(context["pipeline_containers_initial_json"])
    except json.JSONDecodeError:
        context["pipeline_containers_initial_json"] = "[]"


def _post_bpmn(request: HttpRequest, context: Dict[str, Any]) -> None:
    form = BpmnUploadForm(request.POST, request.FILES)
    context["bpmn_form"] = form
    if form.is_valid():
        try:
            bpmn_xml, preview_url, parsed_files, detected_language = generate_bpmn_from_sources(
                uploaded_sources=request.FILES.getlist("sources"),
                uploaded_archive=form.cleaned_data.get("archive"),
                selected_language=form.cleaned_data["language"],
            )
            context["bpmn_xml"] = bpmn_xml
            context["bpmn_parsed_files"] = parsed_files
            context["bpmn_detected_language"] = detected_language
            context["bpmn_preview_url"] = preview_url
        except BpmnGenerationError as e:
            context["bpmn_error_message"] = str(e)
        except Exception as e:
            context["bpmn_error_message"] = f"Erreur interne: {e}"


_POST_HANDLERS: Dict[str, Callable[[HttpRequest, Dict[str, Any]], None]] = {
    "uml": _post_uml,
    "uml_preview": _post_uml_preview,
    "codegen": _post_codegen,
    "pipeline": _post_pipeline,
    "bpmn": _post_bpmn,
}


def build_generation_tools_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Construit le contexte complet pour `generation_tools.html`.

    Comportement identique à l’ancienne `generation_tools_view` monolithique.
    """
    active_tool = resolve_active_tool(request)
    context = _empty_context(active_tool)

    if request.method == "POST":
        handler = _POST_HANDLERS.get(active_tool)
        if handler:
            handler(request, context)

    return context
