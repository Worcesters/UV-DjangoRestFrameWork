from django.shortcuts import render
from django.views import View
from typing import Type, Any
from .form import ContactForm

# Create your views here.
class ContactIndexView(View):
    """
    Page d'accueil du module contact.
    """

    template_name = "contact/form.html"
    form_class: Type[ContactForm] = ContactForm

    def get(self, request, *args, **kwargs):
        """
        Get the contact form.
        Args:
            request: La requête HTTP
            args: Les arguments de la requête
            kwargs: Les paramètres de la requête
        Returns:
            Le contexte de la page
        """
        context: dict[str, ContactForm]  = {
            "form": self.form_class(),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Post the contact form.
        Args:
            request: La requête HTTP
            args: Les arguments de la requête
            kwargs: Les paramètres de la requête
        Returns:
            Le contexte de la page
        """
        form: ContactForm = self.form_class(request.POST)
        context: dict[str, Any] = {
            "form": form,
        }
        return render(request, self.template_name, context)


class ContactSocieteExtraView(View):
    def get(self, request, *args, **kwargs):
        societe = (request.GET.get("societe") or "").strip()
        show = bool(societe)
        # On renvoie un fragment HTML avec le champ `site_web` rendu par Django.
        # `site_web` est optionnel : aucune validation côté HTMX ici.
        form = ContactForm(initial={"societe": societe})
        # renvoie un fragment HTML (pas une page complète)
        return render(
            request,
            "partials/societe_extra.html",
            {"show": show, "societe": societe, "form": form},
        )