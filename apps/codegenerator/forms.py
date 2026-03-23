from django import forms


class CodeGeneratorForm(forms.Form):
    LANGUAGE_CHOICES = (
        ("python", "Python"),
        ("php", "PHP"),
        ("java", "Java"),
    )

    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True,
        initial="python",
        label="Langage cible",
        widget=forms.Select(
            attrs={
                "class": (
                    "w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 "
                    "text-sm font-semibold text-slate-800 shadow-sm "
                    "focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-200"
                )
            }
        ),
    )

    plantuml = forms.CharField(
        required=True,
        label="PlantUML source",
        widget=forms.Textarea(
            attrs={
                "rows": 18,
                "placeholder": (
                    "@startuml\n"
                    "class User {\n"
                    "  +id: int\n"
                    "  +name: string\n"
                    "  +create(email: string): void\n"
                    "}\n"
                    "@enduml"
                ),
                "class": (
                    "w-full min-h-[12rem] max-h-[min(55vh,28rem)] overflow-y-auto rounded-xl "
                    "border border-slate-300 p-3 font-mono text-sm text-slate-800 bg-slate-50 "
                    "focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-200"
                ),
            }
        ),
    )
