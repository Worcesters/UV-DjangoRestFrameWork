import re
from typing import List

from .models import AttributeDef, ClassDef, MethodDef, ParameterDef


class PlantUmlParser:
    _CLASS_BLOCK_RE = re.compile(
        r"(?:(?P<modifier>abstract)\s+)?class\s+(?P<name>\w+)"
        r"(?:\s+extends\s+(?P<parent>\w+))?"
        r"(?:\s+implements\s+(?P<interfaces>[\w\s,]+))?"
        r"\s*\{(?P<body>.*?)\}",
        re.IGNORECASE | re.DOTALL,
    )

    _MEMBER_VIS_RE = re.compile(r"^(?P<vis>[+\-#~])\s*(?P<rest>.+)$")
    _METHOD_RE = re.compile(
        r"^(?P<name>\w+)\((?P<params>[^)]*)\)\s*(?::\s*(?P<ret>[\w\[\]<>.]+))?$"
    )
    _ATTRIBUTE_RE = re.compile(r"^(?P<name>\w+)\s*:\s*(?P<type>[\w\[\]<>.]+)$")
    _PARAM_RE = re.compile(r"^(?P<name>\w+)\s*:\s*(?P<type>[\w\[\]<>.]+)$")

    def parse(self, plantuml_text: str) -> List[ClassDef]:
        classes: List[ClassDef] = []

        for match in self._CLASS_BLOCK_RE.finditer(plantuml_text):
            interfaces_raw = (match.group("interfaces") or "").strip()
            interfaces = [item.strip() for item in interfaces_raw.split(",") if item.strip()]
            class_def = ClassDef(
                name=match.group("name"),
                parent=match.group("parent"),
                is_abstract=bool(match.group("modifier")),
                interfaces=interfaces,
            )
            self._parse_members(match.group("body"), class_def)
            classes.append(class_def)

        return classes

    def _parse_members(self, body: str, class_def: ClassDef) -> None:
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("'") or line.startswith("//"):
                continue

            visibility = "+"
            member_text = line

            vis_match = self._MEMBER_VIS_RE.match(line)
            if vis_match:
                visibility = vis_match.group("vis")
                member_text = vis_match.group("rest").strip()

            member_text, is_abstract = self._extract_abstract_marker(member_text)

            if "(" in member_text and ")" in member_text:
                method = self._parse_method(member_text, visibility, is_abstract=is_abstract)
                if method:
                    class_def.methods.append(method)
                continue

            attribute = self._parse_attribute(member_text, visibility)
            if attribute:
                class_def.attributes.append(attribute)

    def _parse_method(self, line: str, visibility: str, is_abstract: bool = False) -> MethodDef | None:
        match = self._METHOD_RE.match(line)
        if not match:
            return None

        params_text = (match.group("params") or "").strip()
        parameters: List[ParameterDef] = []
        if params_text:
            for item in params_text.split(","):
                param = item.strip()
                if not param:
                    continue
                parsed = self._PARAM_RE.match(param)
                if parsed:
                    parameters.append(
                        ParameterDef(
                            name=parsed.group("name"),
                            type_name=parsed.group("type"),
                        )
                    )
                else:
                    parameters.append(ParameterDef(name=param, type_name="Any"))

        return MethodDef(
            name=match.group("name"),
            parameters=parameters,
            return_type=match.group("ret") or "void",
            visibility=visibility,
            is_abstract=is_abstract,
        )

    def _parse_attribute(self, line: str, visibility: str) -> AttributeDef | None:
        match = self._ATTRIBUTE_RE.match(line)
        if not match:
            return None
        return AttributeDef(
            name=match.group("name"),
            type_name=match.group("type"),
            visibility=visibility,
        )

    def _extract_abstract_marker(self, line: str) -> tuple[str, bool]:
        cleaned = line.replace("{abstract}", "").strip()
        is_abstract = cleaned != line
        if cleaned.lower().startswith("abstract "):
            cleaned = cleaned[9:].strip()
            is_abstract = True
        return cleaned, is_abstract
