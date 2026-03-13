from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class ParameterDef:
    name: str
    type_name: str = "Any"


@dataclass(slots=True)
class AttributeDef:
    name: str
    type_name: str = "Any"
    visibility: str = "+"


@dataclass(slots=True)
class MethodDef:
    name: str
    parameters: List[ParameterDef] = field(default_factory=list)
    return_type: str = "void"
    visibility: str = "+"
    is_abstract: bool = False


@dataclass(slots=True)
class ClassDef:
    name: str
    parent: str | None = None
    is_abstract: bool = False
    is_interface: bool = False
    interfaces: List[str] = field(default_factory=list)
    attributes: List[AttributeDef] = field(default_factory=list)
    methods: List[MethodDef] = field(default_factory=list)
