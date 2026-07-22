from __future__ import annotations

from django import forms

_MAX_ARCHIVE_BYTES = 50 * 1024 * 1024  # 50 Mo (ZIP compressé)


class UmlDispatchForm(forms.Form):
    """Entrées de l'outil de rangement : PlantUML + archive ZIP + renommages."""

    plantuml_text = forms.CharField(
        required=True,
        label="PlantUML source",
        widget=forms.Textarea(
            attrs={
                "id": "id_dispatch_uml",
                "rows": 16,
                "placeholder": (
                    "@startuml\n"
                    "class VersionRepository\n"
                    "VersionRepository --|> ServiceEntityRepository\n"
                    "@enduml"
                ),
                "class": "gen-code-editor gen-code-editor--input",
            }
        ),
    )

    archive = forms.FileField(
        required=True,
        label="Archive ZIP du dossier source",
        widget=forms.ClearableFileInput(attrs={"accept": ".zip"}),
    )

    folder_map = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_archive(self) -> object:
        archive = self.cleaned_data["archive"]
        name = (getattr(archive, "name", "") or "").lower()
        if not name.endswith(".zip"):
            raise forms.ValidationError("Le fichier doit être une archive .zip.")
        if archive.size > _MAX_ARCHIVE_BYTES:
            raise forms.ValidationError("Archive trop volumineuse (max 50 Mo).")
        return archive
