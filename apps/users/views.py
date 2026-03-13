from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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


def generation_tools_view(request):
    from apps.code_converter_uml.forms import UmlUploadForm
    from apps.code_converter_uml.services import (
        UmlGenerationError,
        build_plantuml_preview_url,
        generate_uml_from_upload,
    )
    from apps.codegenerator.forms import CodeGeneratorForm
    from apps.codegenerator.services import CodeGenerationError, generate_code_from_plantuml
    from apps.pipeline_generator.forms import PipelineConfigForm
    from apps.pipeline_generator.services import (
        PipelineGenerationError,
        generate_pipeline_config,
    )
    import json

    tools = [
        {
            "id": "uml",
            "name": "Code to UML",
            "description": "Convertit du code en PlantUML.",
            "url": "/uml/",
            "bg_type": "uml",
            "bg_snippet": "@startuml\nclass Foo {\n  +name: string\n  +run(): void\n}\n@enduml",
            "tags": ["PlantUML", "Code", "Diagrammes"],
        },
        {
            "id": "codegen",
            "name": "UML to Code",
            "description": "Genere du code depuis PlantUML.",
            "url": "/codegenerator/",
            "bg_type": "codegen",
            "bg_snippet": "class Foo(ABC):\n    def run(self) -> None:\n        ...",
            "tags": ["Python", "PHP", "Java", "Génération"],
        },
        {
            "id": "pipeline",
            "name": "Pipeline YML",
            "description": "Genere une pipeline Git/Jenkins avec options avancees.",
            "url": "/pipeline-generator/",
            "bg_type": "pipeline",
            "bg_snippet": "build → test → deploy\n  ↓        ↓       ↓\n clone   lint   release",
            "tags": ["Git", "Jenkins", "CI/CD"],
        },
    ]
    active_tool = request.GET.get("tool") or request.POST.get("tool") or "uml"
    active_tool_name = next((t["name"] for t in tools if t["id"] == active_tool), tools[0]["name"])
    form_action = reverse("users:generation_tools")

    # Contexte par défaut pour chaque outil
    ctx = {
        "tools": tools,
        "active_tool": active_tool,
        "active_tool_name": active_tool_name,
        "form_action": form_action,
        "uml_form": UmlUploadForm(),
        "uml_code": "",
        "preview_url": "",
        "parsed_files": [],
        "detected_language": "",
        "uml_error_message": "",
        "codegen_form": CodeGeneratorForm(),
        "codegen_generated_code": "",
        "codegen_error_message": "",
        "pipeline_form": PipelineConfigForm(),
        "pipeline_generated_config": "",
        "pipeline_error_message": "",
        "pipeline_containers_initial_json": "[]",
    }

    if request.method == "POST":
        if active_tool == "uml":
            form = UmlUploadForm(request.POST, request.FILES)
            ctx["uml_form"] = form
            if form.is_valid():
                try:
                    uml_code, parsed_files, detected_language = generate_uml_from_upload(
                        uploaded_sources=request.FILES.getlist("sources"),
                        uploaded_archive=form.cleaned_data.get("archive"),
                        selected_language=form.cleaned_data["language"],
                    )
                    ctx["uml_code"] = uml_code
                    ctx["preview_url"] = build_plantuml_preview_url(uml_code)
                    ctx["parsed_files"] = parsed_files
                    ctx["detected_language"] = detected_language
                except UmlGenerationError as exc:
                    ctx["uml_error_message"] = str(exc)
                except Exception as exc:
                    ctx["uml_error_message"] = f"Erreur interne lors de l'analyse: {exc}"
        elif active_tool == "codegen":
            form = CodeGeneratorForm(request.POST)
            ctx["codegen_form"] = form
            if form.is_valid():
                try:
                    ctx["codegen_generated_code"] = generate_code_from_plantuml(
                        plantuml_text=form.cleaned_data["plantuml"],
                        language=form.cleaned_data["language"],
                    )
                except CodeGenerationError as exc:
                    ctx["codegen_error_message"] = str(exc)
                except Exception as exc:
                    ctx["codegen_error_message"] = f"Erreur interne de generation: {exc}"
        elif active_tool == "pipeline":
            form = PipelineConfigForm(request.POST)
            ctx["pipeline_form"] = form
            ctx["pipeline_containers_initial_json"] = form.data.get("containers_json", "[]")
            if form.is_valid():
                data = {
                    "project_name": form.cleaned_data["project_name"],
                    "deploy_target": form.cleaned_data["deploy_target"],
                    "use_containers": form.cleaned_data["use_containers"],
                    "command_shell": form.cleaned_data["command_shell"],
                    "use_ssh": form.cleaned_data["use_ssh"],
                    "repo_url": form.cleaned_data.get("repo_url", ""),
                    "deploy_branch": form.cleaned_data.get("deploy_branch", "main"),
                    "env_variables": form.cleaned_data.get("env_variables", ""),
                    "ssh_host": form.cleaned_data.get("ssh_host", ""),
                    "ssh_user": form.cleaned_data.get("ssh_user", ""),
                    "ssh_port": form.cleaned_data.get("ssh_port", "22"),
                    "ssh_key_variable": form.cleaned_data.get("ssh_key_variable", "SSH_PRIVATE_KEY"),
                    "pre_deploy_commands": form.cleaned_data.get("pre_deploy_commands", ""),
                    "deploy_commands": form.cleaned_data.get("deploy_commands", ""),
                    "post_deploy_commands": form.cleaned_data.get("post_deploy_commands", ""),
                    "containers_json": form.cleaned_data.get("containers_json", "[]"),
                }
                try:
                    ctx["pipeline_generated_config"] = generate_pipeline_config(data)
                except PipelineGenerationError as exc:
                    ctx["pipeline_error_message"] = str(exc)
                except Exception as exc:
                    ctx["pipeline_error_message"] = f"Erreur interne de generation: {exc}"
            try:
                json.loads(ctx["pipeline_containers_initial_json"])
            except json.JSONDecodeError:
                ctx["pipeline_containers_initial_json"] = "[]"

    return render(request, "generation_tools.html", ctx)

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
    if not request.user.is_staff:
        return redirect("users:documents")
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
