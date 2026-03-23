"""
Package services utilisateur.

Expose les fonctions historiques (`core`) et les modules dédiés (hub outils, profil public).
"""

from .core import (
    MarkdownDocumentService,
    authenticate_user,
    build_users_display,
    markdown_document_service,
    try_register_user,
)
from .markdown_fs import MarkdownFileDocument
from .generation_tools import build_generation_tools_context
from .public_profile import get_public_profile_context

__all__ = [
    "MarkdownDocumentService",
    "MarkdownFileDocument",
    "authenticate_user",
    "build_generation_tools_context",
    "build_users_display",
    "get_public_profile_context",
    "markdown_document_service",
    "try_register_user",
]
