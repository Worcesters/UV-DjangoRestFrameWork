from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import BpmnUploadForm
from .services import BpmnGenerationError, generate_bpmn_from_sources


@method_decorator(xframe_options_sameorigin, name="dispatch")
class CodeToBpmnIndexView(View):
    """Génération BPMN à partir du code source."""

    template_name = "code_to_bpmn/page.html"
    form_class = BpmnUploadForm

    def get(self, request, *args, **kwargs):
        context = {
            "form": self.form_class(),
            "bpmn_xml": "",
            "preview_url": "",
            "parsed_files": [],
            "detected_language": "",
            "error_message": "",
            "form_action": reverse("code_to_bpmn:index"),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        context = {
            "form": form,
            "bpmn_xml": "",
            "preview_url": "",
            "parsed_files": [],
            "detected_language": "",
            "error_message": "",
            "form_action": reverse("code_to_bpmn:index"),
        }
        if form.is_valid():
            uploaded_sources = request.FILES.getlist("sources")
            uploaded_archive = form.cleaned_data.get("archive")
            selected_language = form.cleaned_data["language"]
            try:
                bpmn_xml, preview_url, parsed_files, detected_language = generate_bpmn_from_sources(
                    uploaded_sources=uploaded_sources,
                    uploaded_archive=uploaded_archive,
                    selected_language=selected_language,
                )
                context["bpmn_xml"] = bpmn_xml
                context["preview_url"] = preview_url
                context["parsed_files"] = parsed_files
                context["detected_language"] = detected_language
            except BpmnGenerationError as exc:
                context["error_message"] = str(exc)
            except Exception as exc:
                context["error_message"] = f"Erreur interne: {exc}"
        return render(request, self.template_name, context)
