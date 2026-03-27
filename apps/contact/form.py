from django import forms

_INPUT_BASE = (
    "w-full px-5 py-3.5 sm:py-4 bg-white border border-slate-200/90 rounded-2xl "
    "text-slate-900 placeholder:text-slate-400 shadow-sm "
    "focus:border-teal-500 focus:ring-4 focus:ring-teal-500/15 "
    "focus:bg-white transition-all outline-none"
)


class ContactForm(forms.Form):
    """
    Formulaire de contact.
    Args:
        forms.Form: Formulaires de Django
    Returns:
        L'objet formulaires de Django
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": _INPUT_BASE,
                "placeholder": "Votre nom",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": _INPUT_BASE,
                "placeholder": "nom@exemple.com",
                "autocomplete": "email",
            }
        ),
    )
    societe = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": _INPUT_BASE,
                "placeholder": "Nom de l'entreprise",
                "autocomplete": "organization",
                # HTMX : charge un fragment après saisie
                # hx-select : obligatoire car le <body> a hx-select="#main-content" (hx-boost) :
                # sans ça, HTMX cherche #main-content dans la réponse fragment → swap vide.
                "hx-get": "/contact/societe-extra/",
                "hx-target": "#societe-extra",
                "hx-select": "#htmx-societe-fragment",
                "hx-swap": "innerHTML",
                # Évite que le <body hx-push-url="true"> remplace l’URL par /contact/societe-extra/?…
                "hx-push-url": "false",
                "hx-trigger": "keyup changed delay:300ms",
            }
        ),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": _INPUT_BASE + " min-h-[160px] resize-y leading-relaxed",
                "placeholder": "Décrivez votre besoin (objectif, contraintes, délais, etc.)",
            }
        )
    )

    # Champ affiché dynamiquement via HTMX dès que `societe` est renseignée.
    # Il reste optionnel côté validation (required=False).
    site_web = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": _INPUT_BASE,
                "placeholder": "https://exemple.com",
                "autocomplete": "url",
            }
        ),
    )

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name:
            raise forms.ValidationError("Le nom est obligatoire.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("L'email est obligatoire.")
        return email

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if not message:
            raise forms.ValidationError("Le message est obligatoire.")
        return message

    def clean_societe(self):
        societe = self.cleaned_data.get("societe")
        if not societe:
            raise forms.ValidationError("La société est obligatoire.")
        return societe
