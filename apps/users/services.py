import hashlib
from typing import Iterable, List, Dict, Tuple, Optional

import markdown
from django.db import IntegrityError
from django.contrib.auth import authenticate

from .models import User, MarkdownDoc


def build_users_display(users: Iterable[User]) -> List[Dict[str, object]]:
    """Construit un affichage anonymisé (pseudo) pour éviter d'exposer les emails."""
    prefixes = [
        "Nova",
        "Orion",
        "Vortex",
        "Nebula",
        "Quantum",
        "Pulse",
        "Cipher",
        "Atlas",
        "Echo",
        "Vertex",
    ]
    suffixes = [
        "Rider",
        "Pilot",
        "Sentinel",
        "Runner",
        "Shadow",
        "Falcon",
        "Comet",
        "Vector",
        "Beacon",
        "Flux",
    ]
    users_display: List[Dict[str, object]] = []
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


def render_markdown(content: str) -> str:
    """Rend du contenu Markdown en HTML."""
    return markdown.markdown(content, extensions=["extra", "nl2br"])


def create_markdown_document(
    *,
    author: User,
    title: str,
    description: str,
    content: str,
) -> MarkdownDoc:
    """Crée et persiste un document MarkdownDoc."""
    return MarkdownDoc.objects.create(
        title=title,
        description=description,
        content=content,
        author=author,
    )


def list_markdown_documents() -> List[MarkdownDoc]:
    """Retourne tous les documents MarkdownDoc triés par date de création."""
    return list(MarkdownDoc.objects.all().order_by("-created_at"))


def try_register_user(email: str, password: str) -> Tuple[bool, Optional[User]]:
    """
    Tente de créer un utilisateur.

    Retourne (success, user_or_none).
    """
    try:
        user = User.objects.create_user(email=email, password=password)
        return True, user
    except IntegrityError:
        return False, None


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Retourne l'utilisateur authentifié ou None."""
    return authenticate(username=email, password=password)

