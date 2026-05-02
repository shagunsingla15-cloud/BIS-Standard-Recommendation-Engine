"""interrogator.py — Category-Aware Contextual Interrogator for vague queries"""

from data.bis_sp21_dataset import VAGUENESS_RULES


# ── Category keyword maps ──────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "steel": [
        "steel", "tmt", "rebar", "reinforcement", "fe 415", "fe 500", "fe 550",
        "fe500", "fe415", "fe550", "bar", "rod", "mild steel", "deformed bar",
        "tor steel", "high yield",
    ],
    "cement": [
        "cement", "opc", "ppc", "psc", "portland", "clinker",
        "53 grade", "43 grade", "33 grade",
    ],
    "concrete": [
        "concrete", "rcc", "pcc", "m20", "m25", "m30", "m35", "m40",
        "mix design", "grade of concrete", "nominal mix", "design mix",
        "reinforced concrete", "plain concrete",
    ],
    "aggregates": [
        "aggregate", "coarse aggregate", "fine aggregate", "sand", "gravel",
        "crushed stone", "grit", "stone chips",
    ],
}

# ── Detail tokens that signal the user already gave enough context ─────────────

_STEEL_DETAIL_TOKENS: list[str] = [
    "seismic", "fe 415", "fe 500", "fe 550", "fe500", "fe415", "fe550",
    "grade", "500d", "fe500d", "ductile", "tmt",
]

_CONCRETE_DETAIL_TOKENS: list[str] = [
    "rcc", "pcc", "reinforced", "plain concrete",
    "mild", "moderate", "severe", "very severe", "extreme",
    "exposure", "m20", "m25", "m30", "m35", "m40",
]

_CEMENT_DETAIL_TOKENS: list[str] = [
    "53", "43", "33", "opc", "ppc", "psc", "portland", "grade",
    "blended", "sulfate", "marine", "coastal",
]

_AGGREGATES_DETAIL_TOKENS: list[str] = [
    "coarse", "fine", "graded", "crushed", "mm", "zone", "river",
]


# ── Category-specific clarification questions ──────────────────────────────────

_CATEGORY_QUESTIONS: dict[str, str] = {
    "steel": (
        "Is this for a seismic zone (Fe 500D) or standard construction? "
        "Please specify the grade: Fe 415 (standard RCC), Fe 500 (high-strength), "
        "or Fe 550 (heavy structures)."
    ),
    "concrete": (
        "Is this for plain concrete (PCC) or reinforced concrete (RCC)? "
        "Please specify the exposure condition: "
        "Mild (indoor/dry), Moderate (humidity/soil), Severe (coastal/freeze-thaw), "
        "Very Severe (seawater/de-icing salts), or Extreme (aggressive chemicals)."
    ),
    "cement": (
        "What grade and type of cement is required? "
        "E.g., OPC 43/53 for general use, PPC for marine or sulfate-rich soil, "
        "PSC for aggressive environments."
    ),
    "aggregates": (
        "Please specify the aggregate type and grading: "
        "coarse (20 mm / 10 mm crushed stone or gravel) or fine (Zone I–IV river sand / M-sand), "
        "and the intended application (RCC slab, concrete block, etc.)."
    ),
}


# ── Public helpers ─────────────────────────────────────────────────────────────

def detect_category(query: str) -> str | None:
    """
    Detect the broad product category from the query using keyword matching.

    Returns one of: "steel", "cement", "concrete", "aggregates", or None.

    Priority order: steel > concrete > cement > aggregates
    (concrete is checked before cement so "concrete" beats the word "cement"
    when both appear, e.g. "cement concrete mix".)
    """
    q = query.lower()
    for category in ("steel", "concrete", "cement", "aggregates"):
        if any(kw in q for kw in _CATEGORY_KEYWORDS[category]):
            return category
    return None


def _detail_present(query: str, category: str) -> bool:
    """Return True if the query already contains sufficient detail for the category."""
    q = query.lower()
    token_map = {
        "steel": _STEEL_DETAIL_TOKENS,
        "concrete": _CONCRETE_DETAIL_TOKENS,
        "cement": _CEMENT_DETAIL_TOKENS,
        "aggregates": _AGGREGATES_DETAIL_TOKENS,
    }
    tokens = token_map.get(category, [])
    return any(t in q for t in tokens)


def get_clarification_question(query: str) -> str:
    """
    Return the category-specific clarification question if the query is vague,
    otherwise return an empty string.

    Logic:
    1. Detect the broad category (steel / cement / concrete / aggregates).
    2. If the user already supplied key details for that category → return "".
    3. Otherwise → return the category-specific question.
    4. If no recognised category is found, fall back to the legacy
       VAGUENESS_RULES table so existing rules (waterproofing, masonry, etc.)
       still fire.
    """
    category = detect_category(query)

    if category is not None:
        if _detail_present(query, category):
            return ""
        return _CATEGORY_QUESTIONS[category]

    # ── Legacy fallback for non-categorised rules (waterproofing, masonry…) ──
    q_lower = query.lower()
    for rule in VAGUENESS_RULES:
        trigger_hit = any(t in q_lower for t in rule["triggers"])
        context_present = any(c.lower() in q_lower for c in rule["context_missing"])
        if trigger_hit and not context_present:
            return rule["question"]

    return ""


# ── Interrogator class (drop-in replacement) ───────────────────────────────────

class ContextualInterrogator:
    """Drop-in replacement for the original ContextualInterrogator."""

    def check_vagueness(self, query: str) -> str:
        """
        Returns a clarifying question string if the query is vague,
        or an empty string if enough context is already present.
        """
        return get_clarification_question(query)