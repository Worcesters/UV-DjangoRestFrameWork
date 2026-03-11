from django.shortcuts import render

from .forms import CodeGeneratorForm
from .services import CodeGenerationError, generate_code_from_plantuml


def index(request):
    context = {
        "form": CodeGeneratorForm(),
        "generated_code": "",
        "error_message": "",
    }

    if request.method == "POST":
        form = CodeGeneratorForm(request.POST)
        context["form"] = form
        if form.is_valid():
            try:
                context["generated_code"] = generate_code_from_plantuml(
                    plantuml_text=form.cleaned_data["plantuml"],
                    language=form.cleaned_data["language"],
                )
            except CodeGenerationError as exc:
                context["error_message"] = str(exc)
            except Exception as exc:  # pragma: no cover
                context["error_message"] = f"Erreur interne de generation: {exc}"

    return render(request, "codegenerator/index.html", context)
