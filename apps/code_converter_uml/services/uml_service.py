import os
import ast
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Tuple, Dict, Any

ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(ENGINE_ROOT) not in sys.path:
    # Permet aux imports historiques "Definition.*", "ParserModule.*", etc.
    # de fonctionner depuis l'app Django.
    sys.path.insert(0, str(ENGINE_ROOT))

try:
    from Definition.Language import Language as ExternalLanguage  # type: ignore
    from ParserModule.Factory import ParserFactory  # type: ignore
    from ParserModule.ParserManager import ParserManager  # type: ignore
    Language = ExternalLanguage
except ModuleNotFoundError:
    # Fallback local: on garde au minimum le support Python sans dépendances externes.
    from enum import Enum

    class LocalLanguage(Enum):
        PYTHON = "python"
        PHP = "php"
        JAVA = "java"

    Language = LocalLanguage
    ParserFactory = None
    ParserManager = None


SUPPORTED_EXTENSIONS = {
    ".py": Language.PYTHON,
    ".php": Language.PHP,
    ".java": Language.JAVA,
}

LANGUAGE_BY_NAME = {
    "python": Language.PYTHON,
    "php": Language.PHP,
    "java": Language.JAVA,
}


class UmlGenerationError(Exception):
    pass


def _safe_extract_zip(zip_path: str, destination: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            target_path = os.path.abspath(os.path.join(destination, member.filename))
            if not target_path.startswith(os.path.abspath(destination)):
                raise UmlGenerationError("Archive zip invalide: chemin dangereux detecte.")
        archive.extractall(destination)


def _normalize_uploaded_path(uploaded_name: str, keep_directories: bool) -> str:
    normalized = uploaded_name.replace("\\", "/")
    parts = [part for part in PurePosixPath(normalized).parts if part not in {"", ".", ".."}]

    if not parts:
        return "uploaded_file"

    if keep_directories:
        return os.path.join(*parts)
    return parts[-1]


def _write_uploaded_files(
    uploaded_files: Iterable,
    output_dir: str,
    keep_directories: bool = False,
) -> List[str]:
    saved_paths: List[str] = []
    for uploaded in uploaded_files:
        relative_path = _normalize_uploaded_path(uploaded.name, keep_directories=keep_directories)
        file_path = os.path.abspath(os.path.join(output_dir, relative_path))
        output_root = os.path.abspath(output_dir)
        if os.path.commonpath([file_path, output_root]) != output_root:
            raise UmlGenerationError("Chemin de fichier uploade invalide detecte.")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as handle:
            for chunk in uploaded.chunks():
                handle.write(chunk)
        saved_paths.append(file_path)
    return saved_paths


def _read_text_with_fallback(file_path: str) -> str:
    # Ordre de fallback pragmatique pour projets FR/Windows.
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return Path(file_path).read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    # Ultime filet de sécurité: remplace les caractères invalides.
    return Path(file_path).read_text(encoding="utf-8", errors="replace")


def _collect_supported_files(directory: str) -> List[str]:
    supported_files: List[str] = []
    for root, _, files in os.walk(directory):
        for file_name in files:
            suffix = Path(file_name).suffix.lower()
            if suffix in SUPPORTED_EXTENSIONS:
                supported_files.append(os.path.join(root, file_name))
    return sorted(supported_files)


def _detect_language(file_paths: List[str], selected_language: str) -> Any:
    if selected_language != "auto":
        try:
            return LANGUAGE_BY_NAME[selected_language]
        except KeyError as exc:
            raise UmlGenerationError(f"Langage non supporte: {selected_language}") from exc

    detected = {SUPPORTED_EXTENSIONS.get(Path(file_path).suffix.lower()) for file_path in file_paths}
    detected.discard(None)

    if not detected:
        raise UmlGenerationError("Aucun fichier .py, .php ou .java detecte dans la selection.")

    if len(detected) > 1:
        raise UmlGenerationError(
            "Selection multi-langage detectee. Choisis un langage explicite pour l'analyse."
        )

    return detected.pop()


def _parse_files(file_paths: List[str], language: Any) -> str:
    if ParserFactory is not None and ParserManager is not None:
        parser_factory = ParserFactory.get_instance(language)
        parsers = parser_factory.get_parsers()

        parser_manager = ParserManager()
        parser_manager.set_parser(parsers)

        # Certains fichiers sources peuvent être cp1252/latin-1.
        # On les convertit temporairement en UTF-8 pour éviter les crashes decode.
        with tempfile.TemporaryDirectory(prefix="uml_parse_utf8_") as temp_dir:
            temp_root = Path(temp_dir)
            base_root = Path(file_paths[0]).parent if file_paths else Path(".")
            normalized_paths: List[str] = []
            for original_path in file_paths:
                original = Path(original_path)
                rel = original.relative_to(base_root)
                target = temp_root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                content = _read_text_with_fallback(str(original))
                target.write_text(content, encoding="utf-8")
                normalized_paths.append(str(target))

            try:
                parser_manager.parse_file(normalized_paths)
                return parser_manager.registry.get_root().element.buildUml()
            except RecursionError as exc:
                # Le parseur externe Python peut boucler sur certains decorators/annotations.
                # Dans ce cas on bascule proprement vers l'analyse AST interne.
                if language == Language.PYTHON:
                    return _parse_python_files(file_paths)
                raise UmlGenerationError(
                    "Recursion detectee pendant l'analyse. "
                    "Essaie un lot de fichiers plus petit."
                ) from exc
            except Exception as exc:
                if language == Language.PYTHON:
                    # Fallback de robustesse pour conserver un resultat UML exploitable.
                    return _parse_python_files(file_paths)
                raise UmlGenerationError(f"Erreur du moteur de parsing externe: {exc}") from exc

    if language == Language.PYTHON:
        # Fallback robuste si moteur externe indisponible.
        return _parse_python_files(file_paths)

    if ParserFactory is None or ParserManager is None:
        raise UmlGenerationError(
            "Le parseur externe pour ce langage n'est pas disponible. "
            "Installe les modules ParserModule/Definition ou utilise Python."
        )
    raise UmlGenerationError("Impossible de parser les fichiers fournis.")


def _node_to_text(node: ast.AST | None) -> str:
    if node is None:
        return "Any"
    try:
        return ast.unparse(node)
    except Exception:
        return "Any"


def _extract_instance_attrs_from_init(func: ast.FunctionDef | ast.AsyncFunctionDef) -> List[Tuple[str, str]]:
    attrs: Dict[str, str] = {}
    for stmt in ast.walk(func):
        if isinstance(stmt, ast.AnnAssign):
            target = stmt.target
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                attrs[target.attr] = _node_to_text(stmt.annotation)
        elif isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if (
                    isinstance(t, ast.Attribute)
                    and isinstance(t.value, ast.Name)
                    and t.value.id == "self"
                ):
                    attrs[t.attr] = attrs.get(t.attr, "Any")
    return [(name, attrs[name]) for name in sorted(attrs.keys())]


def _format_params(args: ast.arguments) -> List[str]:
    formatted: List[str] = []

    all_args = list(args.posonlyargs) + list(args.args)
    defaults_offset = len(all_args) - len(args.defaults)
    for idx, arg in enumerate(all_args):
        if arg.arg in {"self", "cls"}:
            continue
        arg_type = _node_to_text(arg.annotation) if arg.annotation else "Any"
        default_text = ""
        if idx >= defaults_offset:
            default_node = args.defaults[idx - defaults_offset]
            default_text = f" = {_node_to_text(default_node)}"
        formatted.append(f"{arg.arg}: {arg_type}{default_text}")

    if args.vararg:
        vararg_type = _node_to_text(args.vararg.annotation) if args.vararg.annotation else "Any"
        formatted.append(f"*{args.vararg.arg}: {vararg_type}")

    for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
        kw_type = _node_to_text(kwarg.annotation) if kwarg.annotation else "Any"
        default_text = f" = {_node_to_text(default)}" if default is not None else ""
        formatted.append(f"{kwarg.arg}: {kw_type}{default_text}")

    if args.kwarg:
        kwarg_type = _node_to_text(args.kwarg.annotation) if args.kwarg.annotation else "Any"
        formatted.append(f"**{args.kwarg.arg}: {kwarg_type}")

    return formatted


def _parse_python_files(file_paths: List[str]) -> str:
    classes: Dict[str, Dict[str, Any]] = {}
    functions: Dict[str, str] = {}
    inheritance: List[Tuple[str, str]] = []

    for file_path in file_paths:
        source = _read_text_with_fallback(file_path)

        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise UmlGenerationError(f"Erreur de syntaxe Python dans '{Path(file_path).name}': {exc}") from exc

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = ", ".join(_format_params(node.args))
                ret_type = _node_to_text(node.returns) if node.returns else "Any"
                prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
                functions[node.name] = f"+{prefix}{node.name}({params}): {ret_type}"

            if isinstance(node, ast.ClassDef):
                class_name = node.name
                class_info = classes.setdefault(
                    class_name,
                    {"attrs": {}, "methods": {}, "bases": []},
                )
                for base in node.bases:
                    base_name = _node_to_text(base).split(".")[-1]
                    class_info["bases"].append(base_name)
                    inheritance.append((base_name, class_name))

                for body_item in node.body:
                    if isinstance(body_item, ast.AnnAssign) and isinstance(body_item.target, ast.Name):
                        class_info["attrs"][body_item.target.id] = _node_to_text(body_item.annotation)
                    elif isinstance(body_item, ast.Assign):
                        for target in body_item.targets:
                            if isinstance(target, ast.Name):
                                class_info["attrs"][target.id] = class_info["attrs"].get(target.id, "Any")
                    elif isinstance(body_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = ", ".join(_format_params(body_item.args))
                        ret_type = _node_to_text(body_item.returns) if body_item.returns else "Any"
                        prefix = "async " if isinstance(body_item, ast.AsyncFunctionDef) else ""
                        class_info["methods"][body_item.name] = f"+{prefix}{body_item.name}({params}): {ret_type}"
                        if body_item.name == "__init__":
                            for attr_name, attr_type in _extract_instance_attrs_from_init(body_item):
                                class_info["attrs"][attr_name] = class_info["attrs"].get(attr_name, attr_type)

    lines = [
        "@startuml",
        "skinparam classAttributeIconSize 0",
        "hide empty members",
    ]

    if not classes and not functions:
        lines.append("class InputCode {")
        lines.append("  +Aucune structure Python detectee")
        lines.append("}")
    else:
        for class_name in sorted(classes.keys()):
            info = classes[class_name]
            lines.append(f"class {class_name} {{")
            for attr_name in sorted(info["attrs"].keys()):
                lines.append(f"  +{attr_name}: {info['attrs'][attr_name]}")
            for method_name in sorted(info["methods"].keys()):
                lines.append(f"  {info['methods'][method_name]}")
            lines.append("}")

        if functions:
            lines.append("class ModuleFunctions {")
            for fn_name in sorted(functions.keys()):
                lines.append(f"  {functions[fn_name]}")
            lines.append("}")

        for parent, child in sorted(set(inheritance)):
            if parent in classes:
                lines.append(f"{parent} <|-- {child}")

    lines.append("@enduml")
    return "\n".join(lines)


def generate_uml_from_upload(
    uploaded_sources: Iterable,
    uploaded_archive,
    selected_language: str = "auto",
) -> Tuple[str, List[str], str]:
    with tempfile.TemporaryDirectory(prefix="uml_upload_") as temp_dir:
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir, exist_ok=True)

        _write_uploaded_files(uploaded_sources, input_dir, keep_directories=True)

        if uploaded_archive:
            archive_name = os.path.basename(uploaded_archive.name)
            archive_path = os.path.join(temp_dir, archive_name)
            with open(archive_path, "wb") as handle:
                for chunk in uploaded_archive.chunks():
                    handle.write(chunk)
            _safe_extract_zip(archive_path, input_dir)

        files_to_parse = _collect_supported_files(input_dir)
        if not files_to_parse:
            raise UmlGenerationError("Aucun fichier pris en charge trouve.")

        language = _detect_language(files_to_parse, selected_language)
        uml_code = _parse_files(files_to_parse, language)
        relative_names = [os.path.relpath(path, input_dir) for path in files_to_parse]
        detected_language = language.value if hasattr(language, "value") else str(language)
        return uml_code, relative_names, detected_language
