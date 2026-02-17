from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from .models import User, MarkdownDoc
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
import markdown

def index(request):
    """
    Affiche la page d'accueil

    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec la liste des utilisateurs
    """
    users = User.objects.all().order_by('-date_joined')
    documents = MarkdownDoc.objects.all().order_by('-created_at')
    return render(request, "index.html", {"users": users, "documents": documents})

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
        return render(request, "partials/user_form.html", {"active_tab": "signup", "users": users})
    return render(request, "users/signup.html", {"users": users})

def user_list_partial(request):
    """
    Renvoie uniquement le fragment HTML du tableau des utilisateurs
    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec le tableau des utilisateurs
    """

    users = User.objects.all().order_by('-date_joined') # Les plus récents en premier
    return render(request, "partials/user_table.html", {"users": users})

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