from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import UmlUploadForm
from .services import UmlGenerationError, build_plantuml_preview_url, generate_uml_from_upload


@xframe_options_sameorigin
def index(request):
    context = {
        "form": UmlUploadForm(),
        "uml_code": "",
        "preview_url": "",
        "parsed_files": [],
        "detected_language": "",
        "error_message": "",
        "form_action": reverse("code_converter_uml:index"),
    }

    if request.method == "POST":
        form = UmlUploadForm(request.POST, request.FILES)
        context["form"] = form

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

    return render(request, "code_converter_uml/page.html", context)
