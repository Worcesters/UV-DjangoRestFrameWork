import re
from typing import List, Tuple

from .models import AttributeDef, ClassDef, MethodDef, ParameterDef


class PlantUmlParser:
    # Body autorise { ... } à l'intérieur (ex: {abstract}) pour ne pas tronquer au premier }
    _BODY_PATTERN = r"(?:[^{}]|\{[^}]*\})*"
    _INTERFACE_BLOCK_RE = re.compile(
        r"interface\s+(?P<name>\w+)\s*\{(?P<body>" + _BODY_PATTERN + r")\}",
        re.IGNORECASE | re.DOTALL,
    )
    _CLASS_BLOCK_RE = re.compile(
        r"(?:(?P<modifier>abstract)\s+)?class\s+(?P<name>\w+)"
        r"(?:\s+extends\s+(?P<parent>\w+))?"
        r"(?:\s+implements\s+(?P<interfaces>[\w\s,]+))?"
        r"\s*\{(?P<body>" + _BODY_PATTERN + r")\}",
        re.IGNORECASE | re.DOTALL,
    )

    _MEMBER_VIS_RE = re.compile(r"^(?P<vis>[+\-#~])\s*(?P<rest>.+)$")
    _METHOD_RE = re.compile(
        r"^(?P<name>\w+)\((?P<params>[^)]*)\)\s*(?::\s*(?P<ret>[\w\[\]<>.\\]+))?$"
    )
    # Type optionnel : l'UML Builder peut produire un attribut sans type (ex. "- password").
    _ATTRIBUTE_RE = re.compile(r"^(?P<name>\w+)(?:\s*:\s*(?P<type>[\w\[\]<>.\\]+))?$")
    _PARAM_RE = re.compile(r"^(?P<name>\w+)(?:\s*:\s*(?P<type>[\w\[\]<>.\\]+))?$")

    # Relations : tolèrent les directions PlantUML (-up-, -down-, -left-, -right-)
    # et l'absence de label. Triangle plein = héritage (extends),
    # triangle pointillé = réalisation (implements).
    _GEN_CHILD_PARENT_RE = re.compile(
        r"([\w\\$]+)\s*-{1,2}(?:up|down|left|right)?-{0,2}\|>\s*([\w\\$]+)",
        re.IGNORECASE,
    )
    _GEN_PARENT_CHILD_RE = re.compile(
        r"([\w\\$]+)\s*<\|-{0,2}(?:up|down|left|right)?-{1,2}\s*([\w\\$]+)",
        re.IGNORECASE,
    )
    _IMPL_IFACE_CLASS_RE = re.compile(
        r"([\w\\$]+)\s*<\|[-.]*(?:up|down|left|right)?[-.]*\.\.+\s*([\w\\$]+)",
        re.IGNORECASE,
    )
    _IMPL_CLASS_IFACE_RE = re.compile(
        r"([\w\\$]+)\s*\.\.+[-.]*(?:up|down|left|right)?[-.]*\|>\s*([\w\\$]+)",
        re.IGNORECASE,
    )

    def parse(self, plantuml_text: str) -> List[ClassDef]:
        classes: List[ClassDef] = []

        # Interfaces d'abord (pour que le code généré les définisse avant les classes qui les implémentent)
        for match in self._INTERFACE_BLOCK_RE.finditer(plantuml_text):
            class_def = ClassDef(
                name=match.group("name"),
                parent=None,
                is_abstract=True,
                is_interface=True,
                interfaces=[],
            )
            self._parse_members(match.group("body"), class_def)
            for method in class_def.methods:
                method.is_abstract = True
            classes.append(class_def)

        for match in self._CLASS_BLOCK_RE.finditer(plantuml_text):
            interfaces_raw = (match.group("interfaces") or "").strip()
            interfaces = [item.strip() for item in interfaces_raw.split(",") if item.strip()]
            class_def = ClassDef(
                name=match.group("name"),
                parent=match.group("parent"),
                is_abstract=bool(match.group("modifier")),
                is_interface=False,
                interfaces=interfaces,
            )
            self._parse_members(match.group("body"), class_def)
            classes.append(class_def)

        self._apply_implements_relations(plantuml_text, classes)
        edges = self._collect_inheritance_edges(plantuml_text)
        self._apply_extends_from_edges(classes, edges)
        self._ensure_stub_classes(classes, edges)
        return classes

    @staticmethod
    def _normalize_class_name(raw: str) -> str:
        """PlantUML autorise \\Exception (PHP) : on normalise en Exception pour la génération."""
        s = raw.strip()
        while s.startswith("\\"):
            s = s[1:]
        return s

    def _collect_inheritance_edges(self, plantuml_text: str) -> List[Tuple[str, str]]:
        """Retourne des couples (enfant, parent). Syntaxes PlantUML supportées
        (avec ou sans direction -up-/-down-/-left-/-right-) :
        - Parent <|-- Enfant
        - Enfant --|> Parent
        """
        edges: List[Tuple[str, str]] = []
        # Parent <|-- Child
        for m in self._GEN_PARENT_CHILD_RE.finditer(plantuml_text):
            parent = self._normalize_class_name(m.group(1))
            child = self._normalize_class_name(m.group(2))
            edges.append((child, parent))
        # Child --|> Parent
        for m in self._GEN_CHILD_PARENT_RE.finditer(plantuml_text):
            child = self._normalize_class_name(m.group(1))
            parent = self._normalize_class_name(m.group(2))
            edges.append((child, parent))
        return edges

    def _apply_extends_from_edges(
        self, classes: List[ClassDef], edges: List[Tuple[str, str]]
    ) -> None:
        for child, parent in edges:
            for c in classes:
                if c.name == child and not c.is_interface:
                    c.parent = parent
                    break

    def _ensure_stub_classes(
        self, classes: List[ClassDef], edges: List[Tuple[str, str]]
    ) -> None:
        """Classe mentionnée seulement dans une relation d'héritage (sans bloc class) : squelette."""
        known = {c.name for c in classes}
        for child, parent in edges:
            if child in known:
                continue
            classes.append(
                ClassDef(
                    name=child,
                    parent=parent,
                    is_abstract=False,
                    is_interface=False,
                    interfaces=[],
                )
            )
            known.add(child)

    def _apply_implements_relations(self, plantuml_text: str, classes: List[ClassDef]) -> None:
        """Remplit `interfaces` depuis la réalisation PlantUML (triangle pointillé),
        avec ou sans label et avec ou sans direction :
        - Interface <|.. Class
        - Class ..|> Interface
        """
        by_name = {c.name: c for c in classes}

        def add_impl(interface_name: str, class_name: str) -> None:
            target = by_name.get(class_name)
            if target is not None and not target.is_interface:
                if interface_name not in target.interfaces:
                    target.interfaces.append(interface_name)

        # Interface <|.. Class  (gauche = interface)
        for match in self._IMPL_IFACE_CLASS_RE.finditer(plantuml_text):
            interface_name = self._normalize_class_name(match.group(1))
            class_name = self._normalize_class_name(match.group(2))
            add_impl(interface_name, class_name)
        # Class ..|> Interface  (droite = interface)
        for match in self._IMPL_CLASS_IFACE_RE.finditer(plantuml_text):
            class_name = self._normalize_class_name(match.group(1))
            interface_name = self._normalize_class_name(match.group(2))
            add_impl(interface_name, class_name)

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
            member_text = member_text.strip()
            # Si la ligne commence par un symbole de visibilité (+ - # ~), le retirer pour que _parse_method matche le nom (ex: "{abstract} +renderFile(): string" -> "renderFile(): string")
            if member_text and member_text[0] in "+-#~":
                visibility = member_text[0]
                member_text = member_text[1:].strip()

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
                            type_name=parsed.group("type") or "Any",
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
            type_name=match.group("type") or "Any",
            visibility=visibility,
        )

    def _extract_abstract_marker(self, line: str) -> tuple[str, bool]:
        """Retire {abstract} (insensible à la casse) et retourne (ligne_nettoyée, is_abstract)."""
        is_abstract = bool(re.search(r"\{abstract\}", line, re.IGNORECASE))
        cleaned = re.sub(r"\s*\{abstract\}\s*", " ", line, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if cleaned.lower().startswith("abstract "):
            cleaned = cleaned[9:].strip()
            is_abstract = True
        return cleaned, is_abstract
