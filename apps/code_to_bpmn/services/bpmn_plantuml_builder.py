"""
Génération de BPMN au format PlantUML à partir d'un ProcessFlow.
Responsabilité unique : produire du texte PlantUML à partir du graphe (nœuds + arcs).
"""
from .models import NodeType, ProcessFlow


def build_bpmn_plantuml(flow: ProcessFlow) -> str:
    """
    Construit un diagramme d'activité PlantUML en suivant le graphe.
    Les passerelles (GATEWAY_EXCLUSIVE) avec plusieurs arcs sortants
    donnent des if / elseif / else ; les jonctions (label vide) sont des merge.
    """
    nodes_by_id = {n.id: n for n in flow.nodes}
    # source_id -> [(target_id, edge_label), ...]
    successors: dict[str, list[tuple[str, str]]] = {}
    for e in flow.edges:
        successors.setdefault(e.source_id, []).append((e.target_id, e.label or ""))

    lines: list[str] = []
    lines.append("@startuml")
    lines.append("")

    visited: set[str] = set()

    def _sanitize(text: str) -> str:
        # Evite les erreurs du parseur PlantUML (ex: $_SESSION dans conditions).
        return (
            (text or "")
            .replace("\\", "\\\\")
            .replace("$", "\\$")
            .replace("\n", " ")
            .replace('"', "'")
            .strip()
        )

    def emit_flow(node_id: str) -> None:
        if node_id not in nodes_by_id:
            return
        if node_id in visited:
            return
        visited.add(node_id)
        node = nodes_by_id[node_id]
        succs = successors.get(node_id, [])

        if node.type == NodeType.START:
            lines.append("start")
            for (tid, _) in succs:
                emit_flow(tid)
                break
        elif node.type == NodeType.END:
            lines.append("stop")
        elif node.type == NodeType.TASK:
            label = _sanitize(node.label or "Tâche")
            lines.append(f":{label};")
            for (tid, _) in succs:
                emit_flow(tid)
                break
        elif node.type == NodeType.GATEWAY_EXCLUSIVE:
            if node.label:
                # Passerelle de décision : plusieurs branches
                if len(succs) >= 2:
                    join_id: str | None = None
                    cond = _sanitize(node.label or "condition")
                    for i, (tid, edge_label) in enumerate(succs):
                        branch_label = _sanitize(edge_label or f"branch_{i}")
                        if i == 0:
                            lines.append(f"if ({cond}) then ({branch_label})")
                        elif i < len(succs) - 1:
                            lines.append(f"elseif ({cond}) then ({branch_label})")
                        else:
                            lines.append(f"else ({branch_label})")
                        if tid in nodes_by_id and nodes_by_id[tid].type == NodeType.TASK:
                            task_label = _sanitize(nodes_by_id[tid].label or "Tâche")
                            lines.append(f"  :{task_label};")
                            join_succs = successors.get(tid, [])
                            if join_succs:
                                join_id = join_succs[0][0]
                        else:
                            # Evite une branche vide qui casse parfois le rendu PlantUML.
                            lines.append("  :No-op;")
                            if tid in nodes_by_id and nodes_by_id[tid].type == NodeType.GATEWAY_EXCLUSIVE:
                                join_id = tid
                    lines.append("endif")
                    if join_id:
                        emit_flow(join_id)
                else:
                    for (tid, _) in succs:
                        emit_flow(tid)
                        break
            else:
                for (tid, _) in succs:
                    emit_flow(tid)
                    break

    start_nodes = [n for n in flow.nodes if n.type == NodeType.START]
    if start_nodes:
        emit_flow(start_nodes[0].id)

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)

