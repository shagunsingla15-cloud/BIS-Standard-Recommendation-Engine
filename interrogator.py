"""interrogator.py — Contextual Interrogator for vague queries"""
from data.bis_sp21_dataset import VAGUENESS_RULES

class ContextualInterrogator:
    def check_vagueness(self, query: str) -> str:
        """Returns clarifying question if query is vague, else empty string."""
        q_lower = query.lower()
        for rule in VAGUENESS_RULES:
            trigger_hit = any(t in q_lower for t in rule["triggers"])
            context_present = any(c.lower() in q_lower for c in rule["context_missing"])
            if trigger_hit and not context_present:
                return rule["question"]
        return ""
