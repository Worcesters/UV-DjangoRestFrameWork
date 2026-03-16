from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from .models import User, MarkdownDoc
from django.contrib.auth import login, logout
from . import services

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
    documents = services.list_markdown_documents()
    return render(request, "documents.html", {"documents": documents})


def generation_tools_view(request):
    from django.urls import reverse
    from apps.code_converter_uml.forms import UmlUploadForm
    from apps.code_converter_uml.services import UmlGenerationError, build_plantuml_preview_url, generate_uml_from_upload
    from apps.codegenerator.forms import CodeGeneratorForm
    from apps.codegenerator.services import CodeGenerationError, generate_code_from_plantuml
    from apps.pipeline_generator.forms import PipelineConfigForm
    from apps.pipeline_generator.services import PipelineGenerationError, generate_pipeline_config
    from apps.code_to_bpmn.forms import BpmnUploadForm
    from apps.code_to_bpmn.services import BpmnGenerationError, generate_bpmn_from_sources
    import json

    tools = [
        {
            "id": "uml",
            "name": "Code to UML",
            "description": "Convertit du code en PlantUML.",
            "url": "/uml/",
            "bg_type": "uml",
            "bg_snippet": "class MyClass {\n  + method()\n  - attribute",
        },
        {
            "id": "codegen",
            "name": "CodeGenerator",
            "description": "Genere du code depuis PlantUML.",
            "url": "/codegenerator/",
            "bg_type": "codegen",
            "bg_snippet": "PlantUML\n→ Code",
        },
        {
            "id": "uml_preview",
            "name": "UML Previewer",
            "description": "Visualise & crée un diagramme.",
            "url": "/uml/",
            "bg_type": "uml",
            "bg_snippet": "@startuml\nclass User\nUser -> Service: call()\n@enduml",
        },
        {
            "id": "pipeline",
            "name": "PipelineGenerator",
            "description": "Genere une pipeline Git/Jenkins avec options avancees.",
            "url": "/pipeline-generator/",
            "bg_type": "pipeline",
            "bg_snippet": "git\njenkins",
        },
        {
            "id": "bpmn",
            "name": "Code to BPMN",
            "description": "Genere un diagramme BPMN 2.0 a partir du code.",
            "url": "/code-to-bpmn/",
            "bg_type": "bpmn",
            "bg_snippet": "<process>\n  <task/>",
        },
    ]

    active_tool = request.GET.get("tool", "uml")
    if not any(t["id"] == active_tool for t in tools):
        active_tool = "uml"
    active_tool_name = next((t["name"] for t in tools if t["id"] == active_tool), "Code to UML")
    form_action = reverse("users:generation_tools") + "?tool=" + active_tool

    # Contexte par défaut (GET ou POST sans succès)
    context = {
        "tools": tools,
        "default_tool_url": "/uml/",
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
        "bpmn_form": BpmnUploadForm(),
        "bpmn_xml": "",
        "bpmn_parsed_files": [],
        "bpmn_detected_language": "",
        "bpmn_error_message": "",
        "bpmn_preview_url": "",
    }

    if request.method == "POST":
        if active_tool == "uml":
            form = UmlUploadForm(request.POST, request.FILES)
            context["uml_form"] = form
            if form.is_valid():
                try:
                    uml_code, parsed_files, detected_language = generate_uml_from_upload(
                        uploaded_sources=request.FILES.getlist("sources"),
                        uploaded_archive=form.cleaned_data.get("archive"),
                        selected_language=form.cleaned_data["language"],
                    )
                    context["uml_code"] = uml_code
                    context["preview_url"] = build_plantuml_preview_url(uml_code)
                    context["parsed_files"] = parsed_files
                    context["detected_language"] = detected_language
                except UmlGenerationError as e:
                    context["uml_error_message"] = str(e)
                except Exception as e:
                    context["uml_error_message"] = f"Erreur interne: {e}"

        elif active_tool == "uml_preview":
            uml_text = request.POST.get("uml_text", "").strip()
            context["uml_code"] = uml_text
            if uml_text:
                try:
                    context["preview_url"] = build_plantuml_preview_url(uml_text)
                except Exception as e:
                    context["uml_error_message"] = f"Erreur lors de la génération de la preview: {e}"
            else:
                context["uml_error_message"] = "Merci de coller du PlantUML avant de prévisualiser."

        elif active_tool == "codegen":
            form = CodeGeneratorForm(request.POST)
            context["codegen_form"] = form
            if form.is_valid():
                try:
                    context["codegen_generated_code"] = generate_code_from_plantuml(
                        plantuml_text=form.cleaned_data["plantuml"],
                        language=form.cleaned_data["language"],
                    )
                except CodeGenerationError as e:
                    context["codegen_error_message"] = str(e)
                except Exception as e:
                    context["codegen_error_message"] = f"Erreur interne: {e}"

        elif active_tool == "pipeline":
            form = PipelineConfigForm(request.POST)
            context["pipeline_form"] = form
            context["pipeline_containers_initial_json"] = form.data.get("containers_json", "[]")
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
                    context["pipeline_generated_config"] = generate_pipeline_config(data)
                except PipelineGenerationError as e:
                    context["pipeline_error_message"] = str(e)
                except Exception as e:
                    context["pipeline_error_message"] = f"Erreur interne: {e}"
            try:
                json.loads(context["pipeline_containers_initial_json"])
            except json.JSONDecodeError:
                context["pipeline_containers_initial_json"] = "[]"

        elif active_tool == "bpmn":
            form = BpmnUploadForm(request.POST, request.FILES)
            context["bpmn_form"] = form
            if form.is_valid():
                try:
                    bpmn_xml, preview_url, parsed_files, detected_language = generate_bpmn_from_sources(
                        uploaded_sources=request.FILES.getlist("sources"),
                        uploaded_archive=form.cleaned_data.get("archive"),
                        selected_language=form.cleaned_data["language"],
                    )
                    context["bpmn_xml"] = bpmn_xml
                    context["bpmn_parsed_files"] = parsed_files
                    context["bpmn_detected_language"] = detected_language
                    context["bpmn_preview_url"] = preview_url
                except BpmnGenerationError as e:
                    context["bpmn_error_message"] = str(e)
                except Exception as e:
                    context["bpmn_error_message"] = f"Erreur interne: {e}"

    return render(request, "generation_tools.html", context)

def api_plantuml_preview_url(request):
    """Retourne l'URL de preview PlantUML pour un texte donné (usage modal aide UML)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    uml_text = request.POST.get("uml_text", "").strip()
    if not uml_text:
        return JsonResponse({"error": "uml_text required"}, status=400)
    try:
        from apps.code_converter_uml.services import build_plantuml_preview_url
        preview_url = build_plantuml_preview_url(uml_text)
        return JsonResponse({"preview_url": preview_url})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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
    users = User.objects.all().order_by("-date_joined")
    users_display = services.build_users_display(users)

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        success, _ = services.try_register_user(email=email, password=password)
        if success:
            # MAGIE HTMX : On renvoie UNIQUEMENT le petit formulaire avec succès
            # et on déclenche le rafraîchissement de la liste via le header
            response = render(
                request,
                "partials/user_form.html",
                {"success": True, "active_tab": "signup"},
            )
            response["HX-Trigger"] = "refreshList"
            return response

        # Erreur : on renvoie le fragment du formulaire avec l'erreur
        return render(
            request,
            "partials/user_form.html",
            {
                "errors": {"email": "Cet email est déjà utilisé."},
                "active_tab": "signup",
            },
        )

    # 2. GET : si HTMX (clic onglet), on renvoie le fragment ; sinon la page complète
    if request.headers.get("HX-Request"):
        return render(
            request,
            "partials/user_form.html",
            {"active_tab": "signup", "users_display": users_display},
        )
    return render(request, "users/signup.html", {"users_display": users_display})

def user_list_partial(request):
    """
    Renvoie uniquement le fragment HTML du tableau des utilisateurs
    Args:
        request: La requête HTTP
    Returns:
        Le fragment HTML avec le tableau des utilisateurs
    """

    users = User.objects.all().order_by("-date_joined")  # Les plus récents en premier
    users_display = services.build_users_display(users)
    return render(request, "partials/user_table.html", {"users_display": users_display})

def login_view(request):
    if request.user.is_authenticated:
        if request.headers.get("HX-Request"):
            response = render(request, "partials/user_form.html", {"active_tab": "login"})
            response["HX-Redirect"] = "/"
            return response
        return redirect("index")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = services.authenticate_user(email=email, password=password)

        if user is not None:
            login(request, user)
            # On utilise un header HTMX pour rediriger la page entière
            response = render(
                request,
                "partials/user_form.html",
                {"login_success": True},
            )
            response["HX-Redirect"] = "/"
            return response

        return render(
            request,
            "partials/user_form.html",
            {
                "errors": {"login": "Identifiants invalides"},
                "active_tab": "login",
            },
        )

    # GET : fragment avec formulaire connexion (clic onglet ou chargement direct)
    return render(request, "partials/user_form.html", {"active_tab": "login"})


def logout_view(request):
    """Déconnecte l'utilisateur et redirige vers la page d'inscription."""
    logout(request)
    return redirect("users:signup")


def document_list(request):
    """Liste des documents (pour inclusion HTMX si besoin)."""
    documents = services.list_markdown_documents()
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
        doc = services.create_markdown_document(
            author=request.user,
            title=title,
            description=description,
            content=content,
        )
        return redirect("users:document_detail", slug=doc.slug)
    return render(request, "users/document_form.html", {})


def document_detail(request, slug):
    """Viewer : affiche le document Markdown rendu en HTML."""
    doc = get_object_or_404(MarkdownDoc, slug=slug)
    html_content = services.render_markdown(doc.content)
    return render(
        request,
        "users/document_detail.html",
        {"doc": doc, "html_content": html_content},
    )
