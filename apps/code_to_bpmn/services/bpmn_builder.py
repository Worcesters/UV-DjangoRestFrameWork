"""
Génération BPMN 2.0 XML à partir d'un ProcessFlow.
Responsabilité unique : produire du XML BPMN valide à partir du graphe de flux.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .models import NodeType, ProcessFlow


BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"


def build_bpmn_xml(flow: ProcessFlow) -> str:
    """Construit un document BPMN 2.0 XML à partir du ProcessFlow."""
    root = ET.Element(
        f"{{{BPMN_NS}}}definitions",
        attrib={
            "xmlns": BPMN_NS,
            "id": "Definitions_1",
            "targetNamespace": "http://bpmn.io/schema/bpmn",
        },
    )
    process = ET.SubElement(
        root, f"{{{BPMN_NS}}}process",
        id="Process_1",
        isExecutable="true",
    )
    node_ids = {n.id for n in flow.nodes}
    for node in flow.nodes:
        if node.type == NodeType.START:
            ET.SubElement(
                process, f"{{{BPMN_NS}}}startEvent",
                id=node.id, name=node.label or "Start",
            )
        elif node.type == NodeType.END:
            ET.SubElement(
                process, f"{{{BPMN_NS}}}endEvent",
                id=node.id, name=node.label or "End",
            )
        elif node.type == NodeType.TASK:
            ET.SubElement(
                process, f"{{{BPMN_NS}}}task",
                id=node.id, name=node.label or "Task",
            )
        elif node.type == NodeType.GATEWAY_EXCLUSIVE:
            ET.SubElement(
                process, f"{{{BPMN_NS}}}exclusiveGateway",
                id=node.id, name=node.label or "Gateway",
            )
        else:
            ET.SubElement(
                process, f"{{{BPMN_NS}}}task",
                id=node.id, name=node.label or "Task",
            )

    for edge in flow.edges:
        if edge.source_id in node_ids and edge.target_id in node_ids:
            flow_id = f"Flow_{edge.source_id}_{edge.target_id}".replace(" ", "_")
            ET.SubElement(
                process, f"{{{BPMN_NS}}}sequenceFlow",
                id=flow_id,
                sourceRef=edge.source_id,
                targetRef=edge.target_id,
                name=edge.label or "",
            )

    rough = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="  ", encoding=None)
