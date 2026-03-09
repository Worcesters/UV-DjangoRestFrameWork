from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from .models import User, MarkdownDoc
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
import markdown
import hashlib


def _build_users_display(users):
    """Construit un affichage anonymisé (pseudo) pour éviter d'exposer les emails."""
    prefixes = [
        "Nova", "Orion", "Vortex", "Nebula", "Quantum",
        "Pulse", "Cipher", "Atlas", "Echo", "Vertex",
    ]
    suffixes = [
        "Rider", "Pilot", "Sentinel", "Runner", "Shadow",
        "Falcon", "Comet", "Vector", "Beacon", "Flux",
    ]
    users_display = []
    for user in users:
        digest = hashlib.sha256(f"{user.pk}:{user.email}".encode("utf-8")).hexdigest()
        p_idx = int(digest[0:4], 16) % len(prefixes)
        s_idx = int(digest[4:8], 16) % len(suffixes)
        tag = int(digest[8:12], 16) % 10000
        pseudo = f"{prefixes[p_idx]}-{suffixes[s_idx]}-{tag:04d}"
        users_display.append(
            {
                "pseudo": pseudo,
                "is_staff": user.is_staff,
            }
        )
    return users_display

def index(request):
    """Affiche la page d'accueil (landing avec particles, hero, features)."""
    return render(request, "index.html")


def public_profile_view(request):
    """Profil public type CV interactif."""
    timeline = [
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
    try:
        from apps.experience.models import Experience  # import local pour éviter un couplage fort

        db_experiences = Experience.objects.all().order_by("id")
        if db_experiences:
            timeline = [
                {
                    "period": f"{exp.date_debut} - {exp.date_fin}",
                    "title": exp.titre,
                    "company": exp.entreprise,
                    "summary": exp.description,
                }
                for exp in db_experiences
            ]
    except Exception:
        # Fallback statique si le module experience n'est pas disponible.
        pass

    stack_sections = [
        {"label": "Backend", "items": ["Python", "Django", "Django REST Framework", "PostgreSQL"]},
        {"label": "Frontend", "items": ["HTMX", "TailwindCSS", "JavaScript", "Three.js"]},
        {"label": "Infra / Outils", "items": ["Git", "Docker", "CI/CD", "Linux"]},
    ]

    projects = [
        {
            "name": "Sites événementiels - Loxam & CCE Aix-en-Provence",
            "description": "Développement de divers sites événementiels, dont des réalisations pour Loxam et pour le 5e mondial CCE à Aix-en-Provence.",
            "tags": ["Web", "Événementiel", "Front-end"],
        },
        {
            "name": "Edvance - Création from scratch",
            "description": "Conception et développement d'une solution complète depuis zéro, de la structure technique à la mise en production.",
            "tags": ["From Scratch", "Architecture", "Delivery"],
        },
        {
            "name": "Orange - TMA & outils internes",
            "description": "Maintenance applicative (TMA), développement d'outils internes et amélioration continue des processus métiers.",
            "tags": ["TMA", "Outils internes", "Industrialisation"],
        },
        {
            "name": "Pilotage & support opérationnel",
            "description": "Gestion de campagnes emailing, help desk et missions de chef de projet en coordination avec les équipes métiers.",
            "tags": ["Emailing", "Help Desk", "Chef de projet"],
        },
    ]

    return render(
        request,
        "public_profile.html",
        {
            "timeline": timeline,
            "stack_sections": stack_sections,
            "projects": projects,
        },
    )


def documents_page(request):
    """Page liste des documents Markdown."""
    documents = MarkdownDoc.objects.all().order_by('-created_at')
    return render(request, "documents.html", {"documents": documents})

@api_view(['GET'])
def api_hello(request):
    """
    Répond à une requête HTMX

    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec un message de succès ou d'erreur
    """
    # Si c'est HTMX qui appelle (via hx-get)
    if request.headers.get('HX-Request'):
        return render(request, "partials/hello_response.html")

    # Pour le reste du monde (Mobile, etc.), on garde le JSON
    return Response({"message": "Hello from DRF JSON"})

@login_required # Redirige vers la page de login si pas connecté
def profile_view(request):
    """
    Affiche le profil de l'utilisateur connecté

    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec le profil de l'utilisateur
    """
    return render(request, "users/profile.html")

def signup_view(request):
    """
    Affiche la page d'inscription
    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec la page d'inscription
    """

    # 1. On récupère toujours les users pour l'affichage initial (GET)
    users = User.objects.all().order_by('-date_joined')
    users_display = _build_users_display(users)

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # On crée l'utilisateur
            User.objects.create_user(email=email, password=password)

            # MAGIE HTMX : On renvoie UNIQUEMENT le petit formulaire avec succès
            # et on déclenche le rafraîchissement de la liste via le header
            response = render(request, "partials/user_form.html", {"success": True, "active_tab": "signup"})
            response['HX-Trigger'] = 'refreshList'
            return response

        except IntegrityError:
            # Erreur : on renvoie le fragment du formulaire avec l'erreur
            return render(request, "partials/user_form.html", {
                "errors": {"email": "Cet email est déjà utilisé."},
                "active_tab": "signup"
            })

    # 2. GET : si HTMX (clic onglet), on renvoie le fragment ; sinon la page complète
    if request.headers.get("HX-Request"):
        return render(request, "partials/user_form.html", {"active_tab": "signup", "users_display": users_display})
    return render(request, "users/signup.html", {"users_display": users_display})

def user_list_partial(request):
    """
    Renvoie uniquement le fragment HTML du tableau des utilisateurs
    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec le tableau des utilisateurs
    """

    users = User.objects.all().order_by('-date_joined') # Les plus récents en premier
    users_display = _build_users_display(users)
    return render(request, "partials/user_table.html", {"users_display": users_display})

def login_view(request):
    if request.user.is_authenticated:
        if request.headers.get("HX-Request"):
            response = render(request, "partials/user_form.html", {"active_tab": "login"})
            response["HX-Redirect"] = "/"
            return response
        return redirect("index")

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            # On utilise un header HTMX pour rediriger la page entière
            response = render(request, "partials/user_form.html", {"login_success": True})
            response['HX-Redirect'] = '/'
            return response
        else:
            return render(request, "partials/user_form.html", {
                "errors": {"login": "Identifiants invalides"},
                "active_tab": "login"
            })

    # GET : fragment avec formulaire connexion (clic onglet ou chargement direct)
    return render(request, "partials/user_form.html", {"active_tab": "login"})


def logout_view(request):
    """Déconnecte l'utilisateur et redirige vers la page d'inscription."""
    logout(request)
    return redirect("users:signup")


def document_list(request):
    """Liste des documents (pour inclusion HTMX si besoin)."""
    documents = MarkdownDoc.objects.all().order_by('-created_at')
    return render(request, "partials/document_cards.html", {"documents": documents})


@login_required
def document_create(request):
    """Formulaire d'ajout d'un document .md avec titre, description, contenu."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        content = request.POST.get("content", "")
        if not title:
            return render(
                request,
                "users/document_form.html",
                {"error": "Le titre est obligatoire.", "title": title, "description": description, "content": content},
            )
        doc = MarkdownDoc.objects.create(
            title=title,
            description=description,
            content=content,
            author=request.user,
        )
        return redirect("users:document_detail", slug=doc.slug)
    return render(request, "users/document_form.html", {})


def document_detail(request, slug):
    """Viewer : affiche le document Markdown rendu en HTML."""
    doc = get_object_or_404(MarkdownDoc, slug=slug)
    html_content = markdown.markdown(doc.content, extensions=["extra", "nl2br"])
    return render(
        request,
        "users/document_detail.html",
        {"doc": doc, "html_content": html_content},
    )
