# 🚀 Full-Stack Django 2026

> **Stack :** Python 3.12+ | Django 6.x | HTMX 2.x | DRF | uv
> **Structure :** projet `config/` + applications dans `apps/` (norme projet « plateforme » 2026).

---

## Table des matières {#toc}

1. [Arborescence cible (norme 2026)](#dj-0)
2. [Gestion de projet avec `uv`](#dj-1)
3. [HTMX : les attributs utiles](#dj-2)
4. [Verbes HTTP](#dj-2-verbes)
5. [Ciblage et contenu de la réponse](#dj-2-ciblage)
6. [Comportement et UX](#dj-2-comportement)
7. [Django REST Framework (DRF)](#dj-3)
8. [CSRF + template de base (HTMX)](#dj-4)
9. [Architecture par app (SRP)](#dj-5)
10. [Fichiers statiques et `{% static %}`](#dj-static)
11. [Configuration (`config/settings/base.py`)](#dj-static-config)
12. [Arborescence conseillée](#dj-static-arbo)
13. [Dans un template](#dj-static-template)
14. [Bonnes pratiques 2026](#dj-static-bp)
15. [Script d’initialisation : `init_project.sh`](#dj-init)
16. [Après le script](#dj-init-apres)
17. [Résumé](#dj-resume)

---

## 📐 0. Arborescence cible (norme 2026) {#dj-0}

Séparer **le projet Django** (`config/`) et **les applications métier** (`apps/`) : settings découpés, URLs par app, templates globaux à la racine.

```
projet/
├── manage.py
├── pyproject.toml
├── uv.lock
├── config/                    # Projet Django (settings, urls, wsgi, asgi)
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py        # from .dev import * (ou .prod)
│       ├── base.py            # INSTALLED_APPS, TEMPLATES, STATIC, etc.
│       └── dev.py             # DEBUG, base de données locale
├── apps/                      # Paquet Python parent
│   ├── __init__.py
│   └── users/                 # Exemple d’app : users, blog, api…
│       ├── migrations/
│       ├── services/          # Logique métier (SRP)
│       ├── templates/         # Optionnel si templates propres à l’app
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       └── urls.py
├── templates/                 # Templates globaux (extends base.html)
├── static/
├── content/                   # Optionnel : Markdown, assets éditoriaux
│   └── markdown/
└── .env.example
```

- **`config/`** : point d’entrée Django, **pas** de logique métier lourde ici.
- **`apps/<nom>/`** : une brique fonctionnelle (users, catalogue, facturation…).
- **`templates/`** à la racine : `base.html`, pages partagées ; les apps peuvent aussi avoir leur sous-dossier `templates/`.

---

## 📦 1. Gestion de projet avec `uv` {#dj-1}

`uv` est l’outil standard pour verrouiller les dépendances et lancer les commandes sans activer manuellement le venv.

| Commande | Action |
| :--- | :--- |
| `uv init` | Initialise un projet Python (pyproject + lock). |
| `uv add django djangorestframework whitenoise` | Ajoute les paquets et met à jour `uv.lock`. |
| `uv run python manage.py <cmd>` | Exécute Django dans l’environnement géré par uv. |
| `uv sync` | Réinstalle l’environnement selon `uv.lock`. |
| `uv run ruff check .` | (Optionnel) Lint rapide si `ruff` est en dev. |

---

## ⚡ 2. HTMX : les attributs utiles {#dj-2}

HTMX enrichit le HTML sans framework JS lourd. Ci-dessous, **un exemple minimal** par attribut (chemins d’URL à adapter à tes vues Django).

### Verbes HTTP {#dj-2-verbes}

**`hx-get`** — charge un fragment HTML (liste, détail, formulaire vide).

```html
<button type="button"
        hx-get="/contacts/new/"
        hx-target="#zone-form"
        hx-swap="innerHTML">
  Nouveau contact
</button>
<div id="zone-form"></div>
```

**`hx-post`** — envoie un formulaire (souvent création). Pense au `{% csrf_token %}` dans le `<form>`.

```html
<form hx-post="/contacts/create/" hx-target="#liste" hx-swap="beforeend">
  {% csrf_token %}
  <input name="nom" required>
  <button type="submit">Ajouter</button>
</form>
```

**`hx-put`** — remplacement complet d’une ressource (souvent formulaire d’édition en PUT).

```html
<form hx-put="/contacts/42/" hx-target="#contact-42" hx-swap="outerHTML">
  {% csrf_token %}
  <input name="nom" value="Dupont">
  <button type="submit">Enregistrer</button>
</form>
```

**`hx-patch`** — mise à jour partielle (un ou quelques champs).

```html
<input name="statut" value="actif"
       hx-patch="/contacts/42/"
       hx-trigger="change"
       hx-include="this"
       hx-target="#contact-42"
       hx-swap="outerHTML">
```

**`hx-delete`** — suppression côté serveur.

```html
<button type="button"
        hx-delete="/contacts/42/"
        hx-target="#contact-42"
        hx-swap="outerHTML swap:1s"
        hx-confirm="Supprimer ce contact ?">
  Supprimer
</button>
```

### Ciblage et contenu de la réponse {#dj-2-ciblage}

**`hx-target`** — où injecter la réponse (souvent `#main-content` ou un conteneur local).

```html
<a href="/aide/" hx-get="/aide/" hx-target="#panneau" hx-swap="innerHTML">Aide</a>
<aside id="panneau"></aside>
```

**`hx-swap`** — comment fusionner la réponse (`innerHTML`, `outerHTML`, `beforeend`, `afterbegin`, `delete`, + modificateurs comme `scroll:false`, `show:none`).

```html
<button hx-get="/fragment/" hx-target="#box" hx-swap="innerHTML">Remplacer l’intérieur</button>
<button hx-get="/carte/" hx-target="#carte" hx-swap="outerHTML show:none">Sans scrollIntoView</button>
<div id="box">…</div>
```

**`hx-select`** — ne prend qu’un morceau du HTML renvoyé (ex. page complète mais seul le `<main>` est injecté).

```html
<body hx-boost="true" hx-target="#main-content" hx-select="#main-content" hx-swap="innerHTML">
```

*(Le lien boosté charge une page entière ; HTMX n’extrait que `#main-content`.)*

### Comportement et UX {#dj-2-comportement}

**`hx-boost="true"`** — les liens et formulaires du bloc passent en AJAX (souvent sur `<body>` avec `hx-target` / `hx-select`).

```html
<body hx-boost="true" hx-target="#main-content" hx-select="#main-content" hx-swap="innerHTML" hx-push-url="true">
```

**`hx-trigger`** — précise l’événement (défaut : `click` pour les éléments interactifs, `submit` pour les formulaires).

```html
<input hx-get="/search/" hx-trigger="keyup changed delay:500ms" name="q" hx-target="#resultats">
<div id="resultats"></div>
```

**`hx-push-url="true"`** — met l’URL courante à jour après la requête (historique, lien partageable). Souvent avec `hx-boost`.

```html
<a href="/page-b/" hx-boost="true" hx-push-url="true">Page B</a>
```

**`hx-indicator`** — affiche un élément (souvent avec la classe `htmx-indicator`) pendant le chargement.

```html
<button hx-get="/lent/" hx-indicator="#spinner">Charger</button>
<span id="spinner" class="htmx-indicator hidden">⏳</span>
```

*(Ajoute en CSS : `.htmx-indicator.htmx-request` pour afficher le spinner, ou utilise les classes générées par HTMX sur l’élément déclencheur.)*

**`hx-confirm`** — dialogue navigateur avant d’envoyer la requête.

```html
<button hx-delete="/item/1/" hx-confirm="Confirmer la suppression ?">Supprimer</button>
```

> **Django :** pour POST / PUT / PATCH / DELETE, garde le jeton CSRF (voir § 4) via `htmx:configRequest` ou `{% csrf_token %}` dans les formulaires.

---

## 🔌 3. Django REST Framework (DRF) {#dj-3}

Réserver DRF aux **API** (mobile, partenaires, JS autonome). Pour le rendu HTML, **HTMX + vues Django** suffisent en général.

- **Serializers** : validation / représentation JSON.
- **ViewSets / APIView** : endpoints versionnés.
- **Permissions** : `IsAuthenticated`, `AllowAny`, règles personnalisées.

---

## 🛡️ 4. CSRF + template de base (HTMX) {#dj-4}

Django impose le jeton CSRF sur les requêtes mutantes. Avec HTMX, injectez-le dans les en-têtes :

```html
<script src="https://unpkg.com/htmx.org@2.0.0"></script>
<body hx-boost="true" hx-target="#main-content" hx-select="#main-content" hx-swap="innerHTML" hx-push-url="true">
    {% csrf_token %}
    <main id="main-content">
        {% block content %}{% endblock %}
    </main>
    <script>
        document.body.addEventListener("htmx:configRequest", function (event) {
            event.detail.headers["X-CSRFToken"] = "{{ csrf_token }}";
        });
    </script>
</body>
```

Adaptez `hx-target` / `hx-select` à votre layout (souvent un seul `<main>` mis à jour).

---

## 📂 5. Architecture par app (SRP) {#dj-5}

Dans chaque `apps/<nom>/` :

| Fichier / dossier | Rôle |
| :--- | :--- |
| `models.py` | Schéma de données. |
| `forms.py` | Formulaires Django (pages HTMX). |
| `views.py` | **CBV** : `ListView`, `TemplateView`, `View`, etc. |
| `urls.py` | Routes de l’app ; inclus dans `config/urls.py` via `include()`. |
| `services/` | **Logique métier** (calculs, intégrations, règles) — pas de SQL dans les vues si possible. |
| `serializers.py` | Réservé aux endpoints DRF si besoin. |

`config/urls.py` ne fait qu’**assembler** les `include("apps.users.urls")`, etc.

---

## 🎨 Fichiers statiques et `{% static %}` {#dj-static}

Django sert les **CSS, JS, images et polices** via le système de fichiers statiques. En dev, ils sont lus depuis tes dossiers sources ; en prod, ils sont **collectés** dans un répertoire unique et servis par le serveur (souvent **WhiteNoise** derrière Gunicorn).

### Configuration (`config/settings/base.py`) {#dj-static-config}

| Variable | Rôle typique |
| :--- | :--- |
| **`STATIC_URL`** | Préfixe d’URL publique, ex. `"/static/"` → URLs du type `/static/css/...`. |
| **`STATICFILES_DIRS`** | Liste de dossiers où Django cherche les fichiers **en développement**, ex. `[BASE_DIR / "static"]`. |
| **`STATIC_ROOT`** | Dossier cible du **`collectstatic`** en production (ex. `staticfiles/`). Ne pas versionner ce dossier ; le remplir au déploiement. |
| **`STORAGES["staticfiles"]`** | Backend utilisé pour les fichiers collectés (ex. **WhiteNoise** avec compression / hash de noms). |

En dev (`runserver`), Django sert automatiquement les fichiers listés dans `STATICFILES_DIRS`.
En prod : `python manage.py collectstatic` puis le serveur applique `STATIC_URL` + fichiers dans `STATIC_ROOT`.

### Arborescence conseillée {#dj-static-arbo}

Place tes assets **à la racine du projet**, pas dans `config/` :

```
static/
├── css/
│   └── users/
│       └── markdown_preview.css
├── js/
└── icons/
```

Les chemins dans les templates sont **relatifs à `static/`**, sans le préfixe `static/` dans la chaîne passée à `{% static %}`.

### Dans un template {#dj-static-template}

1. **Charger la librairie de tags** une fois par fichier (souvent en tête du template, ou au début d’un `{% block %}` qui contient des références statiques) :

```django
{% load static %}
```

2. **Référencer un fichier** avec le tag `static` : Django génère l’URL correcte (y compris avec hash en prod si tu utilises un storage manifest).

Exemple réel : feuille de style pour l’aperçu Markdown d’une page document.

```django
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/users/markdown_preview.css' %}">
{% endblock %}

{% block content %}
    {# … contenu HTML … #}
{% endblock %}
```

- **`'css/users/markdown_preview.css'`** correspond au fichier **`static/css/users/markdown_preview.css`** sur le disque.
- Tu peux combiner plusieurs `<link>` ou `<script src="{% static 'js/...' %}">` dans le même bloc.

### Bonnes pratiques 2026 {#dj-static-bp}

- **`{% load static %}`** dans chaque template qui utilise `{% static '...' %}` (ou un parent qui étend déjà un template ayant chargé `static` — en pratique, un `load` explicite en haut du fichier évite les surprises).
- Ne pas coder en dur `/static/css/...` : les chemins peuvent changer (CDN, manifest).
- Vérifier que **`django.contrib.staticfiles`** est dans **`INSTALLED_APPS`** (c’est le cas par défaut avec `startproject`).
- Avec **HTMX** qui remplace des fragments HTML : si le fragment inclut des `<link>` vers de nouveaux CSS, le navigateur les charge ; pour un style global, préfère souvent les liens dans **`base.html`** ou un bloc `extra_css` déjà prévu dans la base.

---

## 🛠️ Script d’initialisation : `init_project.sh` {#dj-init}

Ce script crée **toute la base** : `uv`, projet `config`, paquet `apps`, première app `users`, dossiers `templates/`, `static/`, `content/markdown/`, et un **settings découpé** (`config/settings/base.py` + `dev.py`).

**Utilisation (Linux / macOS / Git Bash) :**

```bash
chmod +x scripts/init_project.sh
./scripts/init_project.sh
```

> Dans ce dépôt, le script est versionné sous **`scripts/init_project.sh`**. Tu peux aussi copier le bloc ci-dessous dans un fichier `init_project.sh` à la racine d’un **nouveau dossier vide** (sans `manage.py`).

> Sous **Windows**, utilisez **Git Bash** ou **WSL** pour exécuter le script. Sinon, reproduisez les étapes à la main en suivant les commentaires du script.

````bash
#!/usr/bin/env bash
# init_project.sh — squelette Django 2026 : config/ + apps/
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

# 6. URLs racine : brancher l’app users sur /
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

# 8. Page d’accueil minimale avec HTMX 2
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
````

### Après le script {#dj-init-apres}

1. Créer un superutilisateur : `uv run python manage.py createsuperuser`
2. Versionner `.gitignore` (venv, `db.sqlite3`, `__pycache__`, `staticfiles/`, `.env`).
3. Pour la **prod**, ajouter `config/settings/prod.py`, variables `SECRET_KEY`, `ALLOWED_HOSTS`, base PostgreSQL, etc.

---

## ✅ Résumé {#dj-resume}

| Objectif | Où ça vit |
| :--- | :--- |
| Configuration globale | `config/settings/` |
| Routes racine | `config/urls.py` |
| Feature « utilisateurs » (exemple) | `apps/users/` |
| Templates partagés | `templates/` |
| Fichiers statiques (`STATICFILES_DIRS`, `{% static %}`) | `static/` — voir § *Fichiers statiques et {% static %}* |
| Contenu Markdown hors BDD (optionnel) | `content/markdown/` |

Tu peux dupliquer le modèle `apps/users` pour `apps/blog`, `apps/api`, etc., et les inclure dans `INSTALLED_APPS` + `config/urls.py`.
