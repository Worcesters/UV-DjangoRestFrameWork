"""Construction du contexte page profil public (CV)."""

from __future__ import annotations

from typing import Any, Dict, List


def _default_timeline() -> List[Dict[str, str]]:
    return [
        {
            "period": "2025 - Aujourd'hui",
            "title": "Fullstack Developer",
            "company": "Freelance / SoloWork",
            "summary": "Conception d'interfaces modernes, APIs Django et expériences 3D interactives orientées performance.",
        },
        {
            "period": "2023 - 2025",
            "title": "Développeur Web",
            "company": "Projets produit",
            "summary": "Création de plateformes web avec authentification, gestion documentaire et automatisation des workflows.",
        },
    ]


def _timeline_from_db() -> List[Dict[str, str]]:
    try:
        from apps.experience.models import Experience  # import local pour éviter un couplage fort

        db_experiences = Experience.objects.all().order_by("id")
        if db_experiences:
            return [
                {
                    "period": f"{exp.date_debut} - {exp.date_fin}",
                    "title": exp.titre,
                    "company": exp.entreprise,
                    "summary": exp.description,
                }
                for exp in db_experiences
            ]
    except Exception:
        pass
    return []


def get_timeline() -> List[Dict[str, str]]:
    """Timeline : priorité à la BDD Experience si disponible, sinon données statiques."""
    from_db = _timeline_from_db()
    if from_db:
        return from_db
    return _default_timeline()


def get_stack_sections() -> List[Dict[str, Any]]:
    return [
        {"label": "Backend", "items": ["Python", "Django", "Django REST Framework", "PostgreSQL"]},
        {"label": "Frontend", "items": ["HTMX", "TailwindCSS", "JavaScript", "Three.js"]},
        {"label": "Infra / Outils", "items": ["Git", "Docker", "CI/CD", "Linux"]},
    ]


def get_projects() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Planification - Conception",
            "description": "Estimation de temps de développement, conception de l'architecture et planification des tâches.",
            "bg_type": "planification",
            "bg_snippet": "@startuml\nactor Client\nClient -> API: Demande\nAPI -> DB: Lire/écrire\nAPI --> Client: Réponse\n@enduml",
            "tags": ["Planification", "Conception (Plantuml, BPMN process)", "Estimation"],
        },
        {
            "name": "Développement",
            "description": "Développement de l'application, implémentation des fonctionnalités et tests.",
            "bg_type": "development",
            "bg_snippet": "class GameFacade:\n    def boot(self):\n        return services.start()\n\nif tests.ok:\n    deploy()",
            "tags": ["Développement", "Implémentation", "Tests"],
        },
        {
            "name": "Documentation",
            "description": "Création de documents Markdown, plantuml, etc. pour la documentation de l'application.",
            "bg_type": "documentation",
            "bg_snippet": "# Runbook\n- architecture\n- incidents\n- onboarding\n\n```bash\npython manage.py check\n```",
            "tags": ["Documentation", "Markdown", "Plantuml", "BPMN process", "Création"],
        },
    ]


def get_public_profile_context() -> Dict[str, Any]:
    """Contexte template `public_profile.html`."""
    return {
        "timeline": get_timeline(),
        "stack_sections": get_stack_sections(),
        "projects": get_projects(),
    }
