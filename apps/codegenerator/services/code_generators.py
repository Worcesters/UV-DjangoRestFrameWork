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
        uses_abc = any(cls.is_abstract or any(method.is_abstract for method in cls.methods) for cls in classes)
        if uses_abc:
            lines.append("from abc import ABC, abstractmethod")
            lines.append("")

        for cls in classes:
            bases: List[str] = []
            if cls.parent:
                bases.append(cls.parent)
            if cls.is_abstract and "ABC" not in bases:
                bases.append("ABC")
            base_decl = f"({', '.join(bases)})" if bases else ""
            lines.append(f"class {cls.name}{base_decl}:")
            if not cls.attributes and not cls.methods:
                lines.append("    pass")
                lines.append("")
                continue

            if cls.attributes:
                params = ", ".join(
                    f"{attr.name}: {self._py_type(attr.type_name)} | None = None"
                    for attr in cls.attributes
                )
                lines.append(f"    def __init__(self, {params}) -> None:")
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
        mapping = {
            "string": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "void": "None",
        }
        return mapping.get(type_name.lower(), type_name)


class PhpCodeGenerator(CodeGenerator):
    def generate(self, classes: List[ClassDef]) -> str:
        lines: List[str] = ["<?php", ""]
        for cls in classes:
            extends = f" extends {cls.parent}" if cls.parent else ""
            class_prefix = "abstract class" if cls.is_abstract else "class"
            lines.append(f"{class_prefix} {cls.name}{extends}")
            lines.append("{")
            for attr in cls.attributes:
                lines.append(
                    f"    {_vis_to_php(attr.visibility)} {self._php_type(attr.type_name)} ${attr.name};"
                )
            if cls.attributes:
                lines.append("")
            for method in cls.methods:
                params = ", ".join(
                    f"{self._php_type(param.type_name)} ${param.name}" for param in method.parameters
                )
                ret = self._php_type(method.return_type)
                method_prefix = "abstract " if method.is_abstract else ""
                signature = (
                    f"    {method_prefix}{_vis_to_php(method.visibility)} "
                    f"function {method.name}({params}): {ret}"
                )
                if method.is_abstract:
                    lines.append(signature + ";")
                else:
                    lines.append(signature)
                    lines.append("    {")
                    lines.append("        // TODO: implement")
                    lines.append("    }")
                lines.append("")
            lines.append("}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _php_type(self, type_name: str) -> str:
        mapping = {
            "string": "string",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "void": "void",
        }
        return mapping.get(type_name.lower(), "mixed")


class JavaCodeGenerator(CodeGenerator):
    def generate(self, classes: List[ClassDef]) -> str:
        chunks: List[str] = []
        for cls in classes:
            extends = f" extends {cls.parent}" if cls.parent else ""
            implements = f" implements {', '.join(cls.interfaces)}" if cls.interfaces else ""
            lines: List[str] = [f"public class {cls.name}{extends}{implements} {{", ""]

            for attr in cls.attributes:
                lines.append(
                    f"    {_vis_to_java(attr.visibility)} {self._java_type(attr.type_name)} {attr.name};"
                )
            if cls.attributes:
                lines.append("")

            for method in cls.methods:
                params = ", ".join(
                    f"{self._java_type(param.type_name)} {param.name}" for param in method.parameters
                )
                ret = self._java_type(method.return_type)
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

    def _java_type(self, type_name: str) -> str:
        mapping = {
            "string": "String",
            "int": "int",
            "float": "double",
            "bool": "boolean",
            "void": "void",
        }
        return mapping.get(type_name.lower(), type_name)

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
