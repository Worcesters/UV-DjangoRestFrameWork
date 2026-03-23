from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import CodeGeneratorForm
from .services import CodeGenerationError, generate_code_from_plantuml


@method_decorator(xframe_options_sameorigin, name="dispatch")
class CodeGeneratorIndexView(View):
    """Génération de code à partir de PlantUML (page intégrée + iframe)."""

    template_name = "codegenerator/page.html"
    form_class = CodeGeneratorForm

    def get(self, request, *args, **kwargs):
        context = {
            "form": self.form_class(),
            "generated_code": "",
            "error_message": "",
            "form_action": reverse("codegenerator:index"),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {
            "form": form,
            "generated_code": "",
            "error_message": "",
            "form_action": reverse("codegenerator:index"),
        }
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
        return render(request, self.template_name, context)
