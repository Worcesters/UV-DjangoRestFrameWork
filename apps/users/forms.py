"""Formulaires utilisateur."""

from django import forms

from .models import User

_INPUT_BASE = (
    "w-full px-5 py-4 bg-gray-50 border-2 border-gray-100 rounded-2xl text-gray-900 "
    "focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 focus:bg-white "
    "transition-all outline-none"
)


class UserForm(forms.ModelForm):
    """Inscription : email, société, mot de passe (le mot de passe n'est pas un champ du modèle)."""

    password = forms.CharField(
        label="Clé d'accès",
        widget=forms.PasswordInput(
            attrs={
                "class": _INPUT_BASE,
                "placeholder": "••••••••",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["email", "societe"]
        labels = {
            "email": "Identifiant Email",
            "societe": "Société",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": _INPUT_BASE,
                    "placeholder": "nom@exemple.com",
                    "autocomplete": "email",
                }
            ),
            "societe": forms.TextInput(
                attrs={
                    "class": _INPUT_BASE,
                    "placeholder": "Nom de l'entreprise",
                    "autocomplete": "organization",
                }
            ),
        }

    field_order = ["email", "societe", "password"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["societe"].required = False
