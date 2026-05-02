"""graph.py — Compliance Dependency Graph"""
from data.bis_sp21_dataset import DEPENDENCY_GRAPH

class ComplianceDependencyGraph:
    def get_dependencies(self, standard_id: str) -> dict:
        return DEPENDENCY_GRAPH.get(standard_id, {"testing": [], "sampling": []})
