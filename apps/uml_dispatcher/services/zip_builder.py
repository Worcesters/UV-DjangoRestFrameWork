"""
Assemblage d'un ZIP réorganisé à partir d'un ZIP source et d'une table de
placement ``nom_de_classe -> dossier``.

Sécurité : lecture en mémoire bornée (anti zip-bomb), rejet des chemins
absolus / ``..`` (anti path-traversal), tout reste non destructif (le ZIP
source n'est jamais modifié).
"""

from __future__ import annotations

import io
import posixpath
import zipfile
from typing import Dict, List, Optional, Set

MISC_FOLDER = "_divers"
OTHER_FOLDER = "_autres"

_MAX_ENTRIES = 5000
_MAX_TOTAL_UNCOMPRESSED = 200 * 1024 * 1024  # 200 Mo décompressés


class ZipDispatchError(Exception):
    """Erreur de lecture / assemblage du ZIP."""


def _safe_rel_path(name: str) -> Optional[str]:
    """Normalise un nom d'entrée ZIP en chemin relatif sûr, ou ``None`` si suspect."""
    normalized = name.replace("\\", "/").lstrip("/")
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        return None
    return "/".join(parts)


def _dedupe_path(path: str, used: Set[str]) -> str:
    """Évite les collisions de chemin en suffixant ``(2)``, ``(3)``… avant l'extension."""
    if path not in used:
        return path
    stem, ext = posixpath.splitext(path)
    index = 2
    candidate = f"{stem} ({index}){ext}"
    while candidate in used:
        index += 1
        candidate = f"{stem} ({index}){ext}"
    return candidate


def _target_path(rel_path: str, placement: Dict[str, str]) -> str:
    """Détermine le chemin de sortie d'un fichier selon la table de placement."""
    filename = posixpath.basename(rel_path)
    stem = posixpath.splitext(filename)[0].lower()
    folder = placement.get(stem)
    if folder is None:
        return posixpath.join(OTHER_FOLDER, rel_path)
    return posixpath.join(folder, filename)


def build_reorganized_zip(zip_bytes: bytes, placement: Dict[str, str]) -> bytes:
    """Produit un nouveau ZIP dont les fichiers sont rangés par dossier de groupe.

    Args:
        zip_bytes: Contenu brut du ZIP source.
        placement: Table ``nom_de_classe(minuscule) -> dossier`` (cf. dispatch_service).

    Returns:
        Le contenu binaire du ZIP réorganisé.

    Raises:
        ZipDispatchError: ZIP invalide ou trop volumineux.
    """
    try:
        source = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ZipDispatchError("Fichier ZIP invalide ou corrompu.") from exc

    infos: List[zipfile.ZipInfo] = [info for info in source.infolist() if not info.is_dir()]
    if len(infos) > _MAX_ENTRIES:
        raise ZipDispatchError("Archive refusée : trop de fichiers (max 5000).")
    if sum(info.file_size for info in infos) > _MAX_TOTAL_UNCOMPRESSED:
        raise ZipDispatchError("Archive refusée : taille décompressée trop grande (max 200 Mo).")

    output = io.BytesIO()
    used_paths: Set[str] = set()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dest:
        for info in infos:
            rel_path = _safe_rel_path(info.filename)
            if rel_path is None:
                continue
            out_path = _dedupe_path(_target_path(rel_path, placement), used_paths)
            used_paths.add(out_path)
            dest.writestr(out_path, source.read(info))
    return output.getvalue()
