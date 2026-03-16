from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import BpmnUploadForm
from .services import BpmnGenerationError, generate_bpmn_from_sources


@xframe_options_sameorigin
def index(request):
    context = {
        "form": BpmnUploadForm(),
        "bpmn_xml": "",
        "preview_url": "",
        "parsed_files": [],
        "detected_language": "",
        "error_message": "",
        "form_action": reverse("code_to_bpmn:index"),
    }

    if request.method == "POST":
        form = BpmnUploadForm(request.POST, request.FILES)
        context["form"] = form

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

    return render(request, "code_to_bpmn/page.html", context)
