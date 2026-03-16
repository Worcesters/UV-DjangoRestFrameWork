"""
Modèles de flux processus pour la génération BPMN.
Responsabilité unique : représenter le graphe de flux (nœuds et arcs).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class NodeType(str, Enum):
    """Type de nœud BPMN."""
    START = "start"
    TASK = "task"
    GATEWAY_EXCLUSIVE = "gateway_exclusive"
    END = "end"


@dataclass
class FlowNode:
    """Un nœud du flux (événement, tâche, passerelle)."""
    id: str
    type: NodeType
    label: str


@dataclass
class FlowEdge:
    """Un arc de flux (source -> cible)."""
    source_id: str
    target_id: str
    label: str = ""


@dataclass
class ProcessFlow:
    """Graphe de flux : nœuds et arcs pour génération BPMN."""
    nodes: List[FlowNode] = field(default_factory=list)
    edges: List[FlowEdge] = field(default_factory=list)

    def add_node(self, node: FlowNode) -> None:
        self.nodes.append(node)

    def add_edge(self, edge: FlowEdge) -> None:
        self.edges.append(edge)
