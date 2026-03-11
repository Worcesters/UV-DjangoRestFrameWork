from django import forms


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    widget = MultiFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super().clean(item, initial) for item in data]


class UmlUploadForm(forms.Form):
    LANGUAGE_CHOICES = (
        ("auto", "Auto"),
        ("python", "Python (Alpha version)"),
        ("php", "PHP"),
        ("java", "Java"),
    )

    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=True,
        initial="auto",
        label="Langage",
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
    sources = MultiFileField(
        required=False,
        label="Sources a analyser",
        widget=MultiFileInput(
            attrs={
                "accept": ".py,.php,.java",
                "multiple": True,
                "class": (
                    "block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2 "
                    "text-sm text-slate-700 file:mr-3 file:rounded-lg file:border-0 "
                    "file:bg-indigo-50 file:px-3 file:py-1.5 file:text-xs file:font-bold "
                    "file:text-indigo-700 hover:file:bg-indigo-100"
                ),
            }
        ),
    )
    archive = forms.FileField(
        required=False,
        label="Dossier zip a analyser",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".zip",
                "class": (
                    "block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2 "
                    "text-sm text-slate-700 file:mr-3 file:rounded-lg file:border-0 "
                    "file:bg-fuchsia-50 file:px-3 file:py-1.5 file:text-xs file:font-bold "
                    "file:text-fuchsia-700 hover:file:bg-fuchsia-100"
                ),
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        sources = self.files.getlist("sources")
        archive = cleaned_data.get("archive")
        if not sources and not archive:
            raise forms.ValidationError(
                "Ajoute au moins une source (fichier/dossier) ou une archive compressee (.zip)."
            )
        return cleaned_data
