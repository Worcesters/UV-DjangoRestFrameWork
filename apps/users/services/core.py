"""Services métier users : auth, affichage liste utilisateurs, documents Markdown (fichiers)."""

from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List, Optional, Tuple

import markdown
from django.contrib.auth import authenticate
from django.db import IntegrityError

from ..models import User
from .markdown_fs import MarkdownFileDocument, get_document, list_documents


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


class MarkdownDocumentService:
    """Lecture des fichiers .md dans MARKDOWN_DOCS_DIR + rendu HTML."""

    def list_ordered(self) -> List[MarkdownFileDocument]:
        return list_documents()

    def get_by_slug(self, slug: str) -> Optional[MarkdownFileDocument]:
        return get_document(slug)

    def render_html(self, content: str) -> str:
        """Rend du Markdown en HTML sécurisé pour affichage (extensions extra + nl2br)."""
        return markdown.markdown(content, extensions=["extra", "nl2br"])


markdown_document_service = MarkdownDocumentService()


def try_register_user(
    email: str,
    password: str,
    *,
    societe: str = "",
) -> Tuple[bool, Optional[User]]:
    """
    Tente de créer un utilisateur.

    Retourne (success, user_or_none).
    """
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            societe=(societe or "").strip(),
        )
        return True, user
    except IntegrityError:
        return False, None


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Retourne l'utilisateur authentifié ou None."""
    return authenticate(username=email, password=password)
