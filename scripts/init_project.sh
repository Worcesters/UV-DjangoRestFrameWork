#!/usr/bin/env bash
# init_project.sh — squelette Django 2026 : config/ + apps/
# Usage : chmod +x init_project.sh && ./init_project.sh  (dans un dossier sans manage.py)
set -euo pipefail

echo "🚀 Initialisation du projet Django (config + apps) avec uv..."

if [[ -f manage.py ]]; then
  echo "❌ Un fichier manage.py existe déjà. Abandon."
  exit 1
fi

# 1. Projet Python + dépendances (dans un dossier vide ou presque)
uv init
uv add django djangorestframework whitenoise markdown

# 2. Projet Django : le package s'appelle « config » (pas « core »)
uv run django-admin startproject config .

# 3. Paquet parent apps/ + première application
mkdir -p apps
touch apps/__init__.py
uv run python manage.py startapp users apps/users

# 4. Arborescence globale
mkdir -p templates/partials static/css static/js content/markdown

# 5. Remplacer settings.py monolithique par config/settings/
rm -f config/settings.py
mkdir -p config/settings

cat > config/settings/__init__.py << 'PY'
from .dev import *  # noqa: F401, F403
PY

cat > config/settings/base.py << 'PY'
"""Paramètres communs (tous environnements)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

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
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
PY

cat > config/settings/dev.py << 'PY'
"""Développement local."""
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
PY

# 6. URLs racine : brancher l'app users sur /
cat > config/urls.py << 'PY'
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.users.urls")),
]
PY

# 7. URLs minimales pour apps/users
mkdir -p apps/users/services
touch apps/users/services/__init__.py

cat > apps/users/urls.py << 'PY'
from django.urls import path
from django.views.generic import TemplateView

app_name = "users"

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
]
PY

cat > apps/users/views.py << 'PY'
# Vues CBV / fonctions : à développer ici.
PY

# 8. Page d'accueil minimale avec HTMX 2
cat > templates/base.html << 'HTML'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Django 2026{% endblock %}</title>
    <script src="https://unpkg.com/htmx.org@2.0.0"></script>
</head>
<body
    hx-boost="true"
    hx-target="#main-content"
    hx-select="#main-content"
    hx-swap="innerHTML"
    hx-push-url="true"
>
    {% csrf_token %}
    <nav style="padding:1rem;border-bottom:1px solid #eee;">
        <a href="/">Accueil</a>
    </nav>
    <main id="main-content">
        {% block content %}{% endblock %}
    </main>
    <script>
        document.body.addEventListener("htmx:configRequest", function (event) {
            event.detail.headers["X-CSRFToken"] = "{{ csrf_token }}";
        });
    </script>
</body>
</html>
HTML

cat > templates/index.html << 'HTML'
{% extends "base.html" %}
{% block title %}Accueil{% endblock %}
{% block content %}
<h1>Projet prêt</h1>
<p>Structure <code>config/</code> + <code>apps/</code> — Django 6 + HTMX 2.</p>
{% endblock %}
HTML

# 9. Migrations initiales
uv run python manage.py migrate

echo ""
echo "✅ Projet créé."
echo "   Lancez : uv run python manage.py runserver"
echo "   Puis ouvrez http://127.0.0.1:8000/"
