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

    ## Etape 1.1 : Quand relancer `uv sync`

    Relance `uv sync` dans ces cas :

    - apres un `git pull` qui modifie `uv.lock`
    - apres modification manuelle de `pyproject.toml`
    - apres suppression/recreation du dossier `.venv`

    ```bash
    uv sync
    ```

    ## Etape 2 : Structure Django

    ```bash
    uv run django-admin startproject config .
    mkdir apps
    ni apps/__init__.py
    uv run python manage.py startapp users apps/users
    ```

    ## Etape 3 : Custom User

    ```python
    from django.contrib.auth.models import AbstractUser
    from django.db import models

    class User(AbstractUser):
        username = None
        email = models.EmailField("Email address", unique=True)
        USERNAME_FIELD = "email"
        REQUIRED_FIELDS = []
    ```

    ## Etape 4 : Settings essentiels

    ```python
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "rest_framework",
        "whitenoise.runserver_nostatic",
        "apps.users",
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        # ...
    ]

    AUTH_USER_MODEL = "users.User"
    ```

    ## Etape 5 : Routing

    ```python
    # config/urls.py
    from django.urls import include, path

    urlpatterns = [
        path("", include("apps.users.urls")),
    ]
    ```

    ## Etape 6 : Lancement

    ```bash
    uv run python manage.py makemigrations users
    uv run python manage.py migrate
    uv run python manage.py collectstatic --noinput
    uv run python manage.py runserver
    ```
    """
).strip()


def seed_docs(apps, schema_editor):
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


def unseed_docs(apps, schema_editor):
    markdown_doc_model = apps.get_model("users", "MarkdownDoc")
    markdown_doc_model.objects.filter(slug="guide-production").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_markdowndoc"),
    ]

    operations = [
        migrations.RunPython(seed_docs, reverse_code=unseed_docs),
    ]