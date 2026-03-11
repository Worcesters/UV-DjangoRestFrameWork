# App Django `application`

Cette app est prete a etre copiee dans un autre projet Django.

## Integration rapide

1. Copie le dossier `application/` dans ton projet Django.
2. Ajoute `"application"` dans `INSTALLED_APPS`.
3. Branche les routes dans ton `urls.py` principal:

```python
from django.urls import include, path

urlpatterns = [
    path("uml/", include("application.urls")),
]
```

4. Verifie que les modules moteur sont accessibles (imports `ParserModule`, `Registry`, `Definition`, `TreeModule`).
5. Lance le serveur et ouvre `/uml/`.

## Option preview PlantUML

Par defaut, la preview utilise:

- `https://www.plantuml.com/plantuml/svg`

Tu peux surcharger dans `settings.py`:

```python
PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml/svg"
```

## Fonctionnalites UI

- Upload multiple de fichiers `.py`, `.php`, `.java`
- Upload d'un dossier via archive `.zip`
- Detection auto du langage (ou selection manuelle)
- Affichage du code PlantUML genere
- Preview SVG propre en dessous
