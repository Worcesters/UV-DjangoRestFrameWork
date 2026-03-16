"""
Orchestration : upload → fichiers → langue → ProcessFlow → BPMN XML.
Responsabilité unique : coordonner les étapes et exposer generate_bpmn_from_sources.
"""
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Tuple

from apps.code_converter_uml.services.plantuml_preview import build_plantuml_preview_url

from .flow_parser import get_parser_for_language
from .models import ProcessFlow
from .bpmn_plantuml_builder import build_bpmn_plantuml


SUPPORTED_EXTENSIONS = {".py": "python", ".php": "php", ".java": "java"}


class BpmnGenerationError(Exception):
    """Erreur lors de la génération BPMN."""


def _safe_extract_zip(zip_path: str, destination: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            target_path = os.path.abspath(os.path.join(destination, member.filename))
            if not target_path.startswith(os.path.abspath(destination)):
                raise BpmnGenerationError("Archive zip invalide: chemin dangereux détecté.")
        archive.extractall(destination)


def _normalize_uploaded_path(uploaded_name: str, keep_directories: bool) -> str:
    normalized = uploaded_name.replace("\\", "/")
    parts = [p for p in PurePosixPath(normalized).parts if p not in {"", ".", ".."}]
    if not parts:
        return "uploaded_file"
    return os.path.join(*parts) if keep_directories else parts[-1]


def _write_uploaded_files(
    uploaded_files: Iterable,
    output_dir: str,
    keep_directories: bool = False,
) -> List[str]:
    saved = []
    for uploaded in uploaded_files:
        rel = _normalize_uploaded_path(uploaded.name, keep_directories=keep_directories)
        file_path = os.path.abspath(os.path.join(output_dir, rel))
        root = os.path.abspath(output_dir)
        if os.path.commonpath([file_path, root]) != root:
            raise BpmnGenerationError("Chemin de fichier uploadé invalide.")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)
        saved.append(file_path)
    return saved


def _collect_supported_files(directory: str) -> List[str]:
    out = []
    for root, _, files in os.walk(directory):
        for name in files:
            if Path(name).suffix.lower() in SUPPORTED_EXTENSIONS:
                out.append(os.path.join(root, name))
    return sorted(out)


def _detect_language(file_paths: List[str], selected_language: str) -> str:
    if selected_language != "auto":
        if selected_language not in ("python", "php", "java"):
            raise BpmnGenerationError(f"Langage non supporté: {selected_language}")
        return selected_language
    detected = {SUPPORTED_EXTENSIONS.get(Path(p).suffix.lower()) for p in file_paths}
    detected.discard(None)
    if not detected:
        raise BpmnGenerationError("Aucun fichier .py, .php ou .java dans la sélection.")
    if len(detected) > 1:
        raise BpmnGenerationError("Sélection multi-langage. Choisissez un langage explicite.")
    return list(detected)[0]


def generate_bpmn_from_sources(
    uploaded_sources: Iterable,
    uploaded_archive,
    selected_language: str = "auto",
) -> Tuple[str, str, List[str], str]:
    """
    Génère du BPMN 2.0 XML à partir des fichiers uploadés (et optionnellement d'une archive ZIP).
    Retourne (xml_bpmn, liste_noms_fichiers_relatifs, langage_détecté).
    """
    with tempfile.TemporaryDirectory(prefix="bpmn_upload_") as temp_dir:
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir, exist_ok=True)
        _write_uploaded_files(uploaded_sources, input_dir, keep_directories=True)
        if uploaded_archive:
            archive_path = os.path.join(temp_dir, os.path.basename(uploaded_archive.name))
            with open(archive_path, "wb") as f:
                for chunk in uploaded_archive.chunks():
                    f.write(chunk)
            _safe_extract_zip(archive_path, input_dir)
        files_to_parse = _collect_supported_files(input_dir)
        if not files_to_parse:
            raise BpmnGenerationError("Aucun fichier pris en charge trouvé.")

        language = _detect_language(files_to_parse, selected_language)
        parser = get_parser_for_language(language)
        flow: ProcessFlow = parser.parse_files(files_to_parse)

        bpmn_plantuml = build_bpmn_plantuml(flow)
        preview_url = build_plantuml_preview_url(bpmn_plantuml) or ""
        relative_names = [os.path.relpath(p, input_dir) for p in files_to_parse]
        return bpmn_plantuml, preview_url, relative_names, language
