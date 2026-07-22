"""
Calcul du plan de rangement : regroupe les classes d'un PlantUML par cible
commune d'héritage / réalisation (« hubs »), afin de séparer les fichiers
correspondants dans des sous-dossiers.

Aucune écriture disque ici : ce module produit uniquement un plan (structures
immuables). L'assemblage du ZIP réorganisé est délégué à ``zip_builder``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from apps.codegenerator.services.plantuml_parser import PlantUmlParser

MISC_FOLDER = "_divers"
_MAX_FOLDER_LEN = 64
_FOLDER_UNSAFE_RE = re.compile(r"[^A-Za-z0-9_\- .]")
_WHITESPACE_RE = re.compile(r"\s+")


class DispatchError(Exception):
    """Erreur de calcul du plan de rangement."""


@dataclass(frozen=True, slots=True)
class DispatchGroup:
    """Un groupe = une cible de relation (hub) et les classes qui y sont liées."""

    target: str
    folder: str
    members: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DispatchPlan:
    """Plan complet : groupes détectés, classes orphelines, ensemble des classes."""

    groups: Tuple[DispatchGroup, ...]
    unlinked: Tuple[str, ...]
    class_names: Tuple[str, ...]


def sanitize_folder_name(name: str, fallback: str) -> str:
    """Nettoie un nom de dossier fourni par l'utilisateur (anti path-traversal).

    Args:
        name: Nom candidat (potentiellement dangereux).
        fallback: Nom de repli si le nettoyage aboutit à un nom vide/invalide.

    Returns:
        Un nom de dossier sûr (une seule composante, sans séparateur ni ``..``).
    """
    cleaned = _FOLDER_UNSAFE_RE.sub("", name or "").strip().strip(".").strip()
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    if not cleaned or cleaned in {".", ".."}:
        return sanitize_folder_name(fallback, "groupe") if fallback else "groupe"
    return cleaned[:_MAX_FOLDER_LEN]


def _collect_edges(plantuml_text: str) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Extrait les arêtes (enfant, cible) et les classes déclarées (avec bloc)."""
    parser = PlantUmlParser()
    classes = parser.parse(plantuml_text)
    edges: List[Tuple[str, str]] = []
    declared: List[str] = []
    seen: set[str] = set()
    for class_def in classes:
        if class_def.is_interface:
            continue
        if class_def.name not in seen:
            declared.append(class_def.name)
            seen.add(class_def.name)
        if class_def.parent:
            edges.append((class_def.name, class_def.parent))
        for interface in class_def.interfaces:
            edges.append((class_def.name, interface))
    return edges, declared


def _assign_members(edges: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """Associe chaque enfant à sa première cible rencontrée (héritage prioritaire)."""
    assigned: set[str] = set()
    members_by_target: Dict[str, List[str]] = {}
    for child, target in edges:
        if child in assigned or child == target:
            continue
        assigned.add(child)
        members_by_target.setdefault(target, []).append(child)
    return members_by_target


def build_dispatch_plan(plantuml_text: str) -> DispatchPlan:
    """Construit le plan de rangement par défaut (nom de dossier = nom de la cible).

    Args:
        plantuml_text: Diagramme PlantUML source.

    Returns:
        Le plan avec groupes triés par nombre de membres décroissant.

    Raises:
        DispatchError: Si aucun contenu exploitable n'est fourni.
    """
    if not plantuml_text or not plantuml_text.strip():
        raise DispatchError("Aucun PlantUML fourni.")

    edges, declared = _collect_edges(plantuml_text)
    members_by_target = _assign_members(edges)
    grouped_members = {m for members in members_by_target.values() for m in members}

    groups = tuple(
        DispatchGroup(
            target=target,
            folder=sanitize_folder_name(target, "groupe"),
            members=tuple(members),
        )
        for target, members in sorted(
            members_by_target.items(), key=lambda kv: (-len(kv[1]), kv[0])
        )
    )

    group_targets = set(members_by_target)
    unlinked = tuple(
        name
        for name in declared
        if name not in grouped_members and name not in group_targets
    )
    return DispatchPlan(groups=groups, unlinked=unlinked, class_names=tuple(declared))


def build_placement(
    plan: DispatchPlan, folder_overrides: Dict[str, str] | None = None
) -> Dict[str, str]:
    """Construit la table ``nom_de_classe(minuscule) -> dossier`` pour le ZIP.

    Args:
        plan: Plan calculé par ``build_dispatch_plan``.
        folder_overrides: Renommages ``{cible: nom_dossier}`` fournis par l'UI.

    Returns:
        Table de placement (clés en minuscules) : hub et membres → dossier du
        groupe ; classes orphelines → ``_divers``.
    """
    overrides = folder_overrides or {}
    placement: Dict[str, str] = {}
    for group in plan.groups:
        folder = sanitize_folder_name(overrides.get(group.target, group.folder), group.target)
        placement[group.target.lower()] = folder
        for member in group.members:
            placement[member.lower()] = folder
    for name in plan.unlinked:
        placement[name.lower()] = MISC_FOLDER
    return placement
