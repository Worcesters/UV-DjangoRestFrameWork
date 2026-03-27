from abc import ABC, abstractmethod
from typing import List

from .models import ClassDef, MethodDef


def _vis_to_python_prefix(_vis: str) -> str:
    return ""


def _vis_to_php(vis: str) -> str:
    return {
        "+": "public",
        "-": "private",
        "#": "protected",
        "~": "public",
    }.get(vis, "public")


def _vis_to_java(vis: str) -> str:
    return _vis_to_php(vis)


class CodeGenerator(ABC):
    @abstractmethod
    def generate(self, classes: List[ClassDef]) -> str:
        raise NotImplementedError


class PythonCodeGenerator(CodeGenerator):
    def generate(self, classes: List[ClassDef]) -> str:
        lines: List[str] = []
        lines.append("from __future__ import annotations")
        lines.append("")
        uses_abc = any(
            cls.is_abstract
            or cls.is_interface
            or cls.interfaces
            or any(method.is_abstract for method in cls.methods)
            for cls in classes
        )
        if uses_abc:
            lines.append("from abc import ABC, abstractmethod")
            lines.append("")

        uses_any = False
        for cls in classes:
            for attr in cls.attributes:
                if self._py_type(attr.type_name) == "Any":
                    uses_any = True
                    break
            for method in cls.methods:
                if self._py_type(method.return_type) == "Any":
                    uses_any = True
                    break
                for p in method.parameters:
                    if self._py_type(p.type_name) == "Any":
                        uses_any = True
                        break
        if uses_any:
            lines.append("from typing import Any")
            lines.append("")

        for cls in classes:
            bases: List[str] = []
            # Ordre voulu : class KoTech(ABC, Ko) — ABC explicite pour les classes abstraites, puis parent.
            if cls.is_abstract or cls.is_interface:
                bases.append("ABC")
            if cls.parent:
                bases.append(cls.parent)
            bases.extend(cls.interfaces)
            base_decl = f"({', '.join(bases)})" if bases else ""
            lines.append(f"class {cls.name}{base_decl}:")
            if not cls.attributes and not cls.methods:
                lines.append("    pass")
                lines.append("")
                continue

            # __init__ : inclure les paramètres du parent et appeler super().__init__(...) si héritage
            if not cls.is_interface and cls.attributes:
                parent_cls = next((c for c in classes if c.name == cls.parent), None)
                parent_attrs = list(parent_cls.attributes) if parent_cls else []
                all_params: List[tuple[str, str]] = []
                for attr in parent_attrs:
                    all_params.append((attr.name, self._py_type(attr.type_name)))
                for attr in cls.attributes:
                    all_params.append((attr.name, self._py_type(attr.type_name)))
                params_str = ", ".join(
                    f"{name}: {typ} | None = None" for name, typ in all_params
                )
                lines.append(f"    def __init__(self, {params_str}) -> None:")
                if parent_attrs:
                    parent_args = ", ".join(attr.name for attr in parent_attrs)
                    lines.append(f"        super().__init__({parent_args})")
                for attr in cls.attributes:
                    lines.append(f"        self.{attr.name} = {attr.name}")
                lines.append("")

            for method in cls.methods:
                signature = self._build_python_signature(method)
                if method.is_abstract:
                    lines.append("    @abstractmethod")
                lines.append(f"    def {signature}:")
                if method.is_abstract:
                    lines.append("        raise NotImplementedError")
                else:
                    lines.append("        pass")
                lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _build_python_signature(self, method: MethodDef) -> str:
        params = ", ".join(
            f"{param.name}: {self._py_type(param.type_name)}" for param in method.parameters
        )
        if params:
            params = ", " + params
        return f"{method.name}(self{params}) -> {self._py_type(method.return_type)}"

    def _py_type(self, type_name: str) -> str:
        """Convertit un type PlantUML en type Python (list[X], Any, etc.)."""
        t = type_name.strip()
        while t.startswith("\\"):
            t = t[1:]
        # List<Container> -> list[Container] (syntaxe Python 3.9+ / __future__ annotations)
        if t.lower().startswith("list<") and t.endswith(">"):
            inner = t[5:-1].strip()
            return f"list[{self._py_type(inner)}]"
        mapping = {
            "string": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "boolean": "bool",
            "void": "None",
            "any": "Any",
        }
        return mapping.get(t.lower(), t)


class PhpCodeGenerator(CodeGenerator):
    def generate(self, classes: List[ClassDef]) -> str:
        lines: List[str] = ["<?php", ""]
        for cls in classes:
            extends = f" extends {self._php_extends_name(cls.parent)}" if cls.parent else ""
            implements = f" implements {', '.join(cls.interfaces)}" if cls.interfaces else ""

            if cls.is_interface:
                lines.append(f"interface {cls.name}{extends}")
                lines.append("{")
                for method in cls.methods:
                    params = ", ".join(
                        f"{self._php_type(param.type_name)} ${param.name}"
                        for param in method.parameters
                    )
                    ret = self._php_type(method.return_type)
                    lines.append(
                        f"    public function {method.name}({params}): {ret};"
                    )
                lines.append("}")
            else:
                class_prefix = "abstract class" if cls.is_abstract else "class"
                lines.append(f"{class_prefix} {cls.name}{extends}{implements}")
                lines.append("{")
                for attr in cls.attributes:
                    php_type, default = self._php_attr_type_and_default(attr.type_name)
                    decl = f"    {_vis_to_php(attr.visibility)} {php_type} ${attr.name}"
                    if default:
                        decl += f" = {default}"
                    decl += ";"
                    lines.append(decl)
                if cls.attributes:
                    lines.append("")
                for method in cls.methods:
                    params = ", ".join(
                        f"{self._php_type(param.type_name)} ${param.name}"
                        for param in method.parameters
                    )
                    ret = self._php_type(method.return_type)
                    vis = _vis_to_php(method.visibility)
                    # Méthode abstraite : déclaration seule (sans corps) pour que les classes enfants sachent qu'elles surchargent un contrat du parent
                    if method.is_abstract:
                        lines.append(f"    abstract {vis} function {method.name}({params}): {ret};")
                    else:
                        lines.append(f"    {vis} function {method.name}({params}): {ret}")
                        lines.append("    {")
                        lines.append("        // TODO: implement")
                        lines.append("    }")
                    lines.append("")
                lines.append("}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _php_extends_name(self, parent: str) -> str:
        """Exception (PlantUML / PHP \\Exception) -> \\Exception pour extends."""
        t = parent.strip()
        while t.startswith("\\"):
            t = t[1:]
        if t == "Exception":
            return "\\Exception"
        return t

    def _php_type(self, type_name: str) -> str:
        t = type_name.strip()
        while t.startswith("\\"):
            t = t[1:]
        mapping = {
            "string": "string",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "boolean": "bool",
            "void": "void",
            "exception": "\\Exception",
        }
        if t == "Exception":
            return "\\Exception"
        return mapping.get(t.lower(), "mixed")

    def _php_attr_type_and_default(self, type_name: str) -> tuple[str, str | None]:
        """Retourne (type PHP, valeur par défaut). Pour List<...> / array, initialise à []."""
        t = type_name.strip()
        if t.lower().startswith("list<") or t.lower() == "array" or "[]" in t:
            return "array", "[]"
        return self._php_type(type_name), None


class JavaCodeGenerator(CodeGenerator):
    def generate(self, classes: List[ClassDef]) -> str:
        uses_list = any(
            self._java_type(attr.type_name).startswith("List<")
            for cls in classes
            for attr in cls.attributes
        ) or any(
            self._java_type(p.type_name).startswith("List<")
            for cls in classes
            for method in cls.methods
            for p in method.parameters
        )
        chunks: List[str] = []
        if uses_list:
            chunks.append("import java.util.List;")
            chunks.append("import java.util.ArrayList;")
            chunks.append("")

        for cls in classes:
            if cls.is_interface:
                extends = f" extends {', '.join(cls.interfaces)}" if cls.interfaces else ""
                lines: List[str] = [f"public interface {cls.name}{extends} {{", ""]
                for method in cls.methods:
                    params = ", ".join(
                        f"{self._java_type(p.type_name)} {p.name}" for p in method.parameters
                    )
                    ret = self._java_type(method.return_type)
                    lines.append(f"    {ret} {method.name}({params});")
                lines.append("}")
            else:
                extends = f" extends {self._java_extends_name(cls.parent)}" if cls.parent else ""
                implements = f" implements {', '.join(cls.interfaces)}" if cls.interfaces else ""
                class_mod = "abstract " if cls.is_abstract else ""
                lines = [f"public {class_mod}class {cls.name}{extends}{implements} {{", ""]

                for attr in cls.attributes:
                    jtype = self._java_type(attr.type_name)
                    decl = f"    {_vis_to_java(attr.visibility)} {jtype} {attr.name}"
                    if jtype.startswith("List<"):
                        decl += " = new ArrayList<>()"
                    decl += ";"
                    lines.append(decl)
                if cls.attributes:
                    lines.append("")

                for method in cls.methods:
                    params = ", ".join(
                        f"{self._java_type(param.type_name)} {param.name}"
                        for param in method.parameters
                    )
                    ret = self._java_type(method.return_type)
                    mod = "abstract " if method.is_abstract else ""
                    if method.is_abstract:
                        lines.append(f"    {_vis_to_java(method.visibility)} {mod}{ret} {method.name}({params});")
                    else:
                        lines.append(
                            f"    {_vis_to_java(method.visibility)} {ret} {method.name}({params}) {{"
                        )
                        if ret != "void":
                            lines.append(f"        return {self._default_java_return(ret)};")
                        lines.append("    }")
                    lines.append("")

                lines.append("}")
            chunks.append("\n".join(lines).strip())
        return "\n\n".join(chunks).strip() + "\n"

    def _java_extends_name(self, parent: str) -> str:
        t = parent.strip()
        while t.startswith("\\"):
            t = t[1:]
        return t

    def _java_type(self, type_name: str) -> str:
        """Convertit un type PlantUML en type Java (List<X>, Object, etc.)."""
        t = type_name.strip()
        while t.startswith("\\"):
            t = t[1:]
        if t.lower().startswith("list<") and t.endswith(">"):
            inner = t[5:-1].strip()
            return f"List<{self._java_type(inner)}>"
        mapping = {
            "string": "String",
            "int": "int",
            "float": "double",
            "bool": "boolean",
            "boolean": "boolean",
            "void": "void",
            "any": "Object",
        }
        return mapping.get(t.lower(), t)

    def _default_java_return(self, ret_type: str) -> str:
        if ret_type in {"int", "long", "short", "byte"}:
            return "0"
        if ret_type in {"double", "float"}:
            return "0.0"
        if ret_type == "boolean":
            return "false"
        if ret_type == "char":
            return "'\\0'"
        return "null"


class CodeGeneratorFactory:
    _GENERATORS: dict[
        str,
        type[PythonCodeGenerator] | type[PhpCodeGenerator] | type[JavaCodeGenerator],
    ] = {
        "python": PythonCodeGenerator,
        "php": PhpCodeGenerator,
        "java": JavaCodeGenerator,
    }

    @classmethod
    def build(cls, language: str) -> CodeGenerator:
        try:
            return cls._GENERATORS[language.lower()]()
        except KeyError as exc:
            raise ValueError(f"Langage non supporte: {language}") from exc
