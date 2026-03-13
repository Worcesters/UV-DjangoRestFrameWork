from textwrap import dedent

from django.db import migrations


GUIDE_CONTENT = dedent(
    """
    # Demarrage rapide

    ## Installation

    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows (PowerShell)
    powershell -c "ir https://astral.sh/uv/install.ps1 | iex"
    ```

    ## Etape 1 : Initialisation avec uv

    ```bash
    mkdir mon_projet_pro && cd mon_projet_pro
    uv init
    uv add django djangorestframework whitenoise django-environ
    uv add --dev ruff
    uv sync
    ```

    ## Etape 1.1 : Quand relancer uv sync

    - apres un git pull qui modifie uv.lock
    - apres modification manuelle de pyproject.toml
    - apres suppression/recreation du .venv

    ```bash
    uv sync
    ```

    ## Etape 2 : Lancement

    ```bash
    uv run python manage.py makemigrations users
    uv run python manage.py migrate
    uv run python manage.py collectstatic --noinput
    uv run python manage.py runserver
    ```
    """
).strip()


def reseed_docs(apps, _schema_editor):
    markdown_doc_model = apps.get_model("users", "MarkdownDoc")
    markdown_doc_model.objects.update_or_create(
        slug="guide-production",
        defaults={
            "title": "Guide UV-Django",
            "description": "Guide de demarrage pour le projet UV-Django",
            "content": GUIDE_CONTENT,
            "author_id": None,
        },
    )


def rollback_reseed_docs(_apps, _schema_editor):
    # Pas de suppression pour eviter de perdre un document deja utilise en prod.
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_seed_docs"),
    ]

    operations = [
        migrations.RunPython(reseed_docs, reverse_code=rollback_reseed_docs),
    ]
