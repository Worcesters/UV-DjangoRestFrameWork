from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import UmlUploadForm
from .services import UmlGenerationError, build_plantuml_preview_url, generate_uml_from_upload


@method_decorator(xframe_options_sameorigin, name="dispatch")
class CodeConverterUmlIndexView(View):
    """Conversion code → PlantUML (page intégrée + iframe)."""

    template_name = "code_converter_uml/page.html"
    form_class = UmlUploadForm

    def get(self, request, *args, **kwargs):
        context = {
            "form": self.form_class(),
            "uml_code": "",
            "preview_url": "",
            "parsed_files": [],
            "detected_language": "",
            "error_message": "",
            "form_action": reverse("code_converter_uml:index"),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        context = {
            "form": form,
            "uml_code": "",
            "preview_url": "",
            "parsed_files": [],
            "detected_language": "",
            "error_message": "",
            "form_action": reverse("code_converter_uml:index"),
        }
        if form.is_valid():
            uploaded_sources = request.FILES.getlist("sources")
            uploaded_archive = form.cleaned_data.get("archive")
            selected_language = form.cleaned_data["language"]
            try:
                uml_code, parsed_files, detected_language = generate_uml_from_upload(
                    uploaded_sources=uploaded_sources,
                    uploaded_archive=uploaded_archive,
                    selected_language=selected_language,
                )
                context["uml_code"] = uml_code
                context["preview_url"] = build_plantuml_preview_url(uml_code)
                context["parsed_files"] = parsed_files
                context["detected_language"] = detected_language
            except UmlGenerationError as exc:
                context["error_message"] = str(exc)
            except Exception as exc:  # pragma: no cover
                context["error_message"] = f"Erreur interne lors de l'analyse: {exc}"
        return render(request, self.template_name, context)
