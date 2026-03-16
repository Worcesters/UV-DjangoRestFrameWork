"""
Parseurs de code source vers ProcessFlow.
Responsabilité unique : extraire un graphe de flux à partir du code (Python, PHP, Java).
"""
import ast
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from .models import FlowEdge, FlowNode, NodeType, ProcessFlow


def _read_text(path: str) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return Path(path).read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError):
            continue
    return Path(path).read_text(encoding="utf-8", errors="replace")


class BaseFlowParser(ABC):
    """Interface des parseurs de flux (SRP : une responsabilité par langage)."""

    @abstractmethod
    def parse_files(self, file_paths: List[str]) -> ProcessFlow:
        """Parse les fichiers et retourne un ProcessFlow."""
        pass


class PythonFlowParser(BaseFlowParser):
    """Extrait le flux d'exécution depuis du code Python (AST)."""

    def parse_files(self, file_paths: List[str]) -> ProcessFlow:
        flow = ProcessFlow()
        node_id = [0]

        def next_id(prefix: str) -> str:
            node_id[0] += 1
            return f"{prefix}_{node_id[0]}"

        start_id = next_id("start")
        flow.add_node(FlowNode(id=start_id, type=NodeType.START, label="Début"))
        prev_id = start_id

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue
            try:
                source = _read_text(file_path)
                tree = ast.parse(source)
                prev_id = self._extract_flow_from_ast(tree, flow, prev_id, next_id)
            except SyntaxError:
                task_id = next_id("task")
                flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=f"Parse: {Path(file_path).name}"))
                flow.add_edge(FlowEdge(prev_id, task_id))
                prev_id = task_id

        end_id = next_id("end")
        flow.add_node(FlowNode(id=end_id, type=NodeType.END, label="Fin"))
        flow.add_edge(FlowEdge(prev_id, end_id))
        return flow

    def _extract_flow_from_ast(
        self,
        tree: ast.AST,
        flow: ProcessFlow,
        prev_id: str,
        next_id,
    ) -> str:
        """Parcourt l'AST (corps du module) et ajoute tâches / gateways au flux."""
        if not isinstance(tree, ast.Module):
            return prev_id
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if node.name == "main" or node.name == "__main__" or node.name == "run":
                    prev_id = self._visit_block(node.body, flow, prev_id, next_id)
            elif isinstance(node, ast.If):
                prev_id = self._visit_if(node, flow, prev_id, next_id)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                name = _call_name(node.value)
                task_id = next_id("task")
                flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=name))
                flow.add_edge(FlowEdge(prev_id, task_id))
                prev_id = task_id
        return prev_id

    def _visit_block(
        self,
        body: list,
        flow: ProcessFlow,
        prev_id: str,
        next_id,
    ) -> str:
        """Visite une suite d'instructions (corps de fonction)."""
        for stmt in body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                name = _call_name(stmt.value)
                task_id = next_id("task")
                flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=name))
                flow.add_edge(FlowEdge(prev_id, task_id))
                prev_id = task_id
            elif isinstance(stmt, ast.If):
                prev_id = self._visit_if(stmt, flow, prev_id, next_id)
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        task_id = next_id("task")
                        flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=f"assign {target.id}"))
                        flow.add_edge(FlowEdge(prev_id, task_id))
                        prev_id = task_id
                        break
        return prev_id

    def _visit_if(self, node: ast.If, flow: ProcessFlow, prev_id: str, next_id) -> str:
        """Traite un if/else comme une passerelle exclusive."""
        gw_id = next_id("gw")
        flow.add_node(FlowNode(id=gw_id, type=NodeType.GATEWAY_EXCLUSIVE, label=_condition_label(node)))
        flow.add_edge(FlowEdge(prev_id, gw_id))
        join_id = next_id("gw_join")
        flow.add_node(FlowNode(id=join_id, type=NodeType.GATEWAY_EXCLUSIVE, label=""))
        then_prev = self._visit_block(node.body, flow, gw_id, next_id)
        flow.add_edge(FlowEdge(then_prev, join_id))
        if node.orelse:
            else_prev = self._visit_block(node.orelse, flow, gw_id, next_id)
            flow.add_edge(FlowEdge(else_prev, join_id))
        else:
            flow.add_edge(FlowEdge(gw_id, join_id))
        return join_id


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return "call"


def _condition_label(node: ast.If) -> str:
    try:
        return ast.unparse(node.test)[:40]
    except Exception:
        return "condition"


class PhpFlowParser(BaseFlowParser):
    """Parseur PHP orienté flux : méthodes, if/else, try/catch et boucles."""

    def parse_files(self, file_paths: List[str]) -> ProcessFlow:
        flow = ProcessFlow()
        node_id = [0]

        def next_id(prefix: str) -> str:
            node_id[0] += 1
            return f"{prefix}_{node_id[0]}"

        start_id = next_id("start")
        flow.add_node(FlowNode(id=start_id, type=NodeType.START, label="Début"))
        end_id = next_id("end")
        flow.add_node(FlowNode(id=end_id, type=NodeType.END, label="Fin"))

        found_methods = False
        prev_id = start_id
        for file_path in file_paths:
            if not file_path.endswith(".php"):
                continue
            source = _read_text(file_path)
            methods = self._extract_methods(source)
            if not methods:
                continue
            found_methods = True
            # Analyse toutes les méthodes dans l'ordre d'apparition du fichier.
            for method_name, method_body in methods.items():
                method_task_id = next_id("task")
                flow.add_node(FlowNode(id=method_task_id, type=NodeType.TASK, label=method_name))
                flow.add_edge(FlowEdge(prev_id, method_task_id))
                prev_id = self._parse_php_segment(method_body, flow, method_task_id, next_id)

        if not found_methods:
            prev_id = start_id
            for file_path in file_paths:
                if not file_path.endswith(".php"):
                    continue
                source = _read_text(file_path)
                for match in re.finditer(r"function\s+(\w+)\s*\([^)]*\)", source):
                    task_id = next_id("task")
                    flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=match.group(1)))
                    flow.add_edge(FlowEdge(prev_id, task_id))
                    prev_id = task_id
        flow.add_edge(FlowEdge(prev_id, end_id))
        return flow

    def _extract_methods(self, source: str) -> dict[str, str]:
        methods: dict[str, str] = {}
        method_pattern = re.compile(
            r"(public|protected|private)\s+function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[\w\\]+)?\s*\{",
            re.IGNORECASE,
        )
        for match in method_pattern.finditer(source):
            method_name = match.group(2)
            open_brace_idx = source.find("{", match.end() - 1)
            if open_brace_idx == -1:
                continue
            close_brace_idx = self._find_matching_brace(source, open_brace_idx)
            if close_brace_idx == -1:
                continue
            methods[method_name] = source[open_brace_idx + 1 : close_brace_idx]
        return methods

    def _pick_entry_method(self, source: str, methods: dict[str, str]) -> str:
        if "displayDetails" in methods:
            return "displayDetails"
        bottom_calls = re.findall(r"\$controller\s*->\s*(\w+)\s*\(", source, re.IGNORECASE)
        for call in bottom_calls:
            if call in methods:
                return call
        public_like = [name for name in methods.keys() if not name.startswith("__")]
        if public_like:
            return public_like[0]
        return next(iter(methods.keys()))

    def _find_matching_brace(self, text: str, open_brace_idx: int) -> int:
        level = 0
        for i in range(open_brace_idx, len(text)):
            char = text[i]
            if char == "{":
                level += 1
            elif char == "}":
                level -= 1
                if level == 0:
                    return i
        return -1

    def _find_matching_paren(self, text: str, open_paren_idx: int) -> int:
        level = 0
        for i in range(open_paren_idx, len(text)):
            char = text[i]
            if char == "(":
                level += 1
            elif char == ")":
                level -= 1
                if level == 0:
                    return i
        return -1

    def _add_calls_from_text(self, text: str, flow: ProcessFlow, prev_id: str, next_id) -> str:
        call_pattern = re.compile(r"(?:\$this|\$controller)\s*->\s*(\w+)\s*\(", re.IGNORECASE)
        for call in call_pattern.findall(text):
            task_id = next_id("task")
            flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=call))
            flow.add_edge(FlowEdge(prev_id, task_id))
            prev_id = task_id
        return prev_id

    def _parse_php_segment(self, segment: str, flow: ProcessFlow, prev_id: str, next_id) -> str:
        pos = 0
        keyword_pattern = re.compile(r"\b(if|try|foreach|for|while)\b", re.IGNORECASE)

        while pos < len(segment):
            match = keyword_pattern.search(segment, pos)
            if not match:
                return self._add_calls_from_text(segment[pos:], flow, prev_id, next_id)

            prev_id = self._add_calls_from_text(segment[pos : match.start()], flow, prev_id, next_id)
            keyword = match.group(1).lower()

            if keyword == "if":
                prev_id, pos = self._parse_if_chain(segment, match.start(), flow, prev_id, next_id)
            elif keyword == "try":
                prev_id, pos = self._parse_try_catch(segment, match.start(), flow, prev_id, next_id)
            else:
                prev_id, pos = self._parse_loop(segment, keyword, match.start(), flow, prev_id, next_id)
        return prev_id

    def _parse_if_chain(self, text: str, start_idx: int, flow: ProcessFlow, prev_id: str, next_id) -> tuple[str, int]:
        paren_start = text.find("(", start_idx)
        if paren_start == -1:
            return prev_id, start_idx + 2
        paren_end = self._find_matching_paren(text, paren_start)
        if paren_end == -1:
            return prev_id, paren_start + 1

        condition = " ".join(text[paren_start + 1 : paren_end].split())[:80]
        block_start = text.find("{", paren_end)
        if block_start == -1:
            return prev_id, paren_end + 1
        block_end = self._find_matching_brace(text, block_start)
        if block_end == -1:
            return prev_id, block_start + 1

        branches: list[tuple[str, str]] = [("YES", text[block_start + 1 : block_end])]
        idx = block_end + 1
        while idx < len(text):
            tail = text[idx:]
            m_elseif = re.match(r"\s*elseif\s*\(", tail, re.IGNORECASE)
            m_else = re.match(r"\s*else\s*\{", tail, re.IGNORECASE)
            if m_elseif:
                elseif_start = idx + m_elseif.end() - 1
                elseif_end = self._find_matching_paren(text, elseif_start)
                if elseif_end == -1:
                    break
                elseif_cond = " ".join(text[elseif_start + 1 : elseif_end].split())[:80]
                elseif_block_start = text.find("{", elseif_end)
                if elseif_block_start == -1:
                    break
                elseif_block_end = self._find_matching_brace(text, elseif_block_start)
                if elseif_block_end == -1:
                    break
                branches.append((elseif_cond, text[elseif_block_start + 1 : elseif_block_end]))
                idx = elseif_block_end + 1
                continue
            if m_else:
                else_block_start = idx + m_else.end() - 1
                else_block_end = self._find_matching_brace(text, else_block_start)
                if else_block_end == -1:
                    break
                branches.append(("NO", text[else_block_start + 1 : else_block_end]))
                idx = else_block_end + 1
            break

        gw_id = next_id("gw")
        join_id = next_id("gw_join")
        flow.add_node(FlowNode(id=gw_id, type=NodeType.GATEWAY_EXCLUSIVE, label=condition or "condition"))
        flow.add_node(FlowNode(id=join_id, type=NodeType.GATEWAY_EXCLUSIVE, label=""))
        flow.add_edge(FlowEdge(prev_id, gw_id))

        for label, body in branches:
            branch_id = next_id("task")
            flow.add_node(FlowNode(id=branch_id, type=NodeType.TASK, label=f"branch {label}"))
            flow.add_edge(FlowEdge(gw_id, branch_id, label=label))
            branch_end = self._parse_php_segment(body, flow, branch_id, next_id)
            flow.add_edge(FlowEdge(branch_end, join_id))

        has_no_branch = any(label.upper() == "NO" for (label, _) in branches)
        if not has_no_branch:
            flow.add_edge(FlowEdge(gw_id, join_id, label="NO"))

        return join_id, idx

    def _parse_try_catch(self, text: str, start_idx: int, flow: ProcessFlow, prev_id: str, next_id) -> tuple[str, int]:
        try_block_start = text.find("{", start_idx)
        if try_block_start == -1:
            return prev_id, start_idx + 3
        try_block_end = self._find_matching_brace(text, try_block_start)
        if try_block_end == -1:
            return prev_id, try_block_start + 1
        try_body = text[try_block_start + 1 : try_block_end]

        catches: list[tuple[str, str]] = []
        idx = try_block_end + 1
        catch_pattern = re.compile(r"\s*catch\s*\(([^)]+)\)\s*\{", re.IGNORECASE)
        while idx < len(text):
            tail = text[idx:]
            m_catch = catch_pattern.match(tail)
            if not m_catch:
                break
            catch_block_start = idx + m_catch.end() - 1
            catch_block_end = self._find_matching_brace(text, catch_block_start)
            if catch_block_end == -1:
                break
            exception_type = m_catch.group(1).strip().split()[0]
            catch_body = text[catch_block_start + 1 : catch_block_end]
            catches.append((exception_type, catch_body))
            idx = catch_block_end + 1

        gw_id = next_id("gw")
        join_id = next_id("gw_join")
        flow.add_node(FlowNode(id=gw_id, type=NodeType.GATEWAY_EXCLUSIVE, label="try/catch"))
        flow.add_node(FlowNode(id=join_id, type=NodeType.GATEWAY_EXCLUSIVE, label=""))
        flow.add_edge(FlowEdge(prev_id, gw_id))

        ok_id = next_id("task")
        flow.add_node(FlowNode(id=ok_id, type=NodeType.TASK, label="branch OK"))
        flow.add_edge(FlowEdge(gw_id, ok_id, label="OK"))
        ok_end = self._parse_php_segment(try_body, flow, ok_id, next_id)
        flow.add_edge(FlowEdge(ok_end, join_id))

        for exception_type, catch_body in catches:
            catch_id = next_id("task")
            flow.add_node(FlowNode(id=catch_id, type=NodeType.TASK, label=f"branch {exception_type}"))
            flow.add_edge(FlowEdge(gw_id, catch_id, label=exception_type))
            catch_end = self._parse_php_segment(catch_body, flow, catch_id, next_id)
            flow.add_edge(FlowEdge(catch_end, join_id))

        return join_id, idx

    def _parse_loop(
        self,
        text: str,
        keyword: str,
        start_idx: int,
        flow: ProcessFlow,
        prev_id: str,
        next_id,
    ) -> tuple[str, int]:
        paren_start = text.find("(", start_idx)
        if paren_start == -1:
            return prev_id, start_idx + len(keyword)
        paren_end = self._find_matching_paren(text, paren_start)
        if paren_end == -1:
            return prev_id, paren_start + 1
        condition = " ".join(text[paren_start + 1 : paren_end].split())[:80]

        block_start = text.find("{", paren_end)
        if block_start == -1:
            return prev_id, paren_end + 1
        block_end = self._find_matching_brace(text, block_start)
        if block_end == -1:
            return prev_id, block_start + 1
        body = text[block_start + 1 : block_end]

        gw_id = next_id("gw")
        join_id = next_id("gw_join")
        flow.add_node(FlowNode(id=gw_id, type=NodeType.GATEWAY_EXCLUSIVE, label=f"{keyword} {condition or 'condition'}"))
        flow.add_node(FlowNode(id=join_id, type=NodeType.GATEWAY_EXCLUSIVE, label=""))
        flow.add_edge(FlowEdge(prev_id, gw_id))

        loop_id = next_id("task")
        flow.add_node(FlowNode(id=loop_id, type=NodeType.TASK, label="branch LOOP"))
        flow.add_edge(FlowEdge(gw_id, loop_id, label="YES"))
        loop_end = self._parse_php_segment(body, flow, loop_id, next_id)
        flow.add_edge(FlowEdge(loop_end, join_id))
        flow.add_edge(FlowEdge(gw_id, join_id, label="NO"))

        return join_id, block_end + 1


class JavaFlowParser(BaseFlowParser):
    """Extrait un flux simplifié depuis du Java (regex)."""

    def parse_files(self, file_paths: List[str]) -> ProcessFlow:
        flow = ProcessFlow()
        node_id = [0]

        def next_id(prefix: str) -> str:
            node_id[0] += 1
            return f"{prefix}_{node_id[0]}"

        start_id = next_id("start")
        flow.add_node(FlowNode(id=start_id, type=NodeType.START, label="Début"))
        prev_id = start_id
        for file_path in file_paths:
            if not file_path.endswith(".java"):
                continue
            source = _read_text(file_path)
            for match in re.finditer(r"(?:public|private|protected)?\s*(?:\w+\s+)+\s+(\w+)\s*\([^)]*\)\s*\{", source):
                task_id = next_id("task")
                flow.add_node(FlowNode(id=task_id, type=NodeType.TASK, label=match.group(1)))
                flow.add_edge(FlowEdge(prev_id, task_id))
                prev_id = task_id
        end_id = next_id("end")
        flow.add_node(FlowNode(id=end_id, type=NodeType.END, label="Fin"))
        flow.add_edge(FlowEdge(prev_id, end_id))
        return flow


def get_parser_for_language(lang: str) -> BaseFlowParser:
    if lang == "python":
        return PythonFlowParser()
    if lang == "php":
        return PhpFlowParser()
    if lang == "java":
        return JavaFlowParser()
    return PythonFlowParser()
