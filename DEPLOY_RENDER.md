# Deploy Django (uv) sur Render

## 1) Prérequis
- Projet pousse sur GitHub.
- Fichier `render.yaml` present a la racine.
- `uv.lock` present (deja dans ce projet).

## 2) Push du code
Depuis la racine du projet:

```powershell
git add .
git commit -m "Prepare Render deployment with uv"
git push origin main
```

## 3) Creation sur Render
1. Ouvrir Render.
2. Cliquer `New` -> `Blueprint`.
3. Selectionner ton repo GitHub.
4. Render detecte `render.yaml` et cree:
   - un service web `uv-django`
   - une base `uv-django-db`

## 4) Variables d'environnement
Verifie dans le service web (Environment):
- `DEBUG=False`
- `SECRET_KEY` (auto-generee)
- `ALLOWED_HOSTS=.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://*.onrender.com`
- `DATABASE_URL` (auto liee a la base)

## 5) Build / Start (deja configures)
- Build:
  - installe `uv`
  - `uv sync --frozen --no-dev`
  - `collectstatic`
  - `migrate`
- Start:
  - `uv run gunicorn config.wsgi:application`

## 6) Verification apres deploy
- Ouvre l'URL du service Render.
- Verifie:
  - la page d'accueil charge
  - la page de jeu charge
  - les assets statiques s'affichent
- Regarde les logs Render:
  - pas d'erreur de migration
  - pas d'erreur static files
  - pas d'erreur `DisallowedHost`

## 7) En cas d'erreur frequente
- `DisallowedHost`: corriger `ALLOWED_HOSTS`.
- `CSRF verification failed`: corriger `CSRF_TRUSTED_ORIGINS`.
- `SECRET_KEY` absent: ajouter la variable dans Render.
- Erreur DB: verifier que `DATABASE_URL` est bien injectee.
