"""
Documents Markdown lus depuis le dossier configuré (MARKDOWN_DOCS_DIR), sans table en base.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.utils import timezone as dj_tz
from django.utils.text import slugify


@dataclass(frozen=True, slots=True)
class MarkdownFileDocument:
    """Représente un fichier .md pour les templates (liste + détail)."""

    slug: str
    title: str
    description: str
    content: str
    created_at: datetime
    updated_at: datetime
    source_path: str  # chemin relatif au dossier pour debug / admin
    author: object | None = None  # réservé (pas d’auteur fichier)


def _docs_root() -> Path:
    return Path(settings.MARKDOWN_DOCS_DIR)


def _parse_title_description(raw: str, stem: str) -> tuple[str, str]:
    """Titre = premier # titre, sinon nom de fichier humanisé ; description = premier bloc de texte."""
    title = stem.replace("-", " ").replace("_", " ").title()
    m = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
    if m:
        title = m.group(1).strip()
    description = ""
    lines = [ln.rstrip() for ln in raw.splitlines()]
    buf: list[str] = []
    for line in lines:
        if not line.strip():
            if buf:
                break
            continue
        if line.startswith("#"):
            continue
        if line.startswith("```"):
            break
        buf.append(line.strip())
        if len(" ".join(buf)) > 500:
            break
    description = " ".join(buf)[:500]
    return title, description


def _assign_slugs(paths: list[Path]) -> dict[str, Path]:
    """Associe un slug URL unique à chaque fichier (.md)."""
    out: dict[str, Path] = {}
    used: set[str] = set()
    for path in sorted(paths):
        base = slugify(path.stem, allow_unicode=True) or "document"
        slug = base
        n = 1
        while slug in used:
            n += 1
            slug = f"{base}-{n}"
        used.add(slug)
        out[slug] = path
    return out


# Fichiers d’aide dans le dossier (non listés comme pages)
_IGNORED_MD = frozenset({"readme.md"})


def slug_path_map() -> dict[str, Path]:
    root = _docs_root()
    if not root.is_dir():
        return {}
    paths = [p for p in root.glob("*.md") if p.name.lower() not in _IGNORED_MD]
    return _assign_slugs(paths)


def _to_doc(path: Path, slug: str, *, load_content: bool) -> MarkdownFileDocument:
    text = path.read_text(encoding="utf-8")
    title, description = _parse_title_description(text, path.stem)
    st = path.stat()
    tz = dj_tz.get_current_timezone()
    ts = datetime.fromtimestamp(st.st_mtime, tz=tz)
    rel = path.name
    try:
        rel = str(path.relative_to(_docs_root()))
    except ValueError:
        pass
    return MarkdownFileDocument(
        slug=slug,
        title=title,
        description=description,
        content=text if load_content else "",
        created_at=ts,
        updated_at=ts,
        source_path=rel,
    )


def list_documents() -> list[MarkdownFileDocument]:
    """Liste les .md du dossier, du plus récent au plus ancien (mtime)."""
    mapping = slug_path_map()
    if not mapping:
        return []
    items = sorted(mapping.items(), key=lambda item: item[1].stat().st_mtime, reverse=True)
    return [_to_doc(path, slug, load_content=False) for slug, path in items]


def get_document(slug: str) -> Optional[MarkdownFileDocument]:
    mapping = slug_path_map()
    path = mapping.get(slug)
    if not path:
        return None
    return _to_doc(path, slug, load_content=True)
