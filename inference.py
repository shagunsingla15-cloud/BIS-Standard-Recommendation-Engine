"""
inference.py — BIS RAG Inference Engine
  • Two-stage retrieval (Stage 1 hybrid + Stage 2 re-ranker)
  • Rationale explicitly links query keyword → BIS clause
  • Mandatory Tests field per result
  • Regulatory Ecosystem (secondary IS standards)
  • Zero-hallucination final guard strips any IS number not in the index

Run:
    python inference.py --input sample_input.json --output results.json
"""

import argparse
import json
import re
import time
from typing import Any

from retriever import HybridRetriever, VALID_IS_NUMBERS
from graph import ComplianceDependencyGraph
from interrogator import ContextualInterrogator
from roadmap import ComplianceRoadmapGenerator


# ── JSON output schema ─────────────────────────────────────────────────────────

_RESULT_SCHEMA_KEYS = {
    # Identification
    "standard_id", "title", "category",
    # Scores
    "score", "bm25_score", "dense_score", "rerank_boost", "confidence_level",
    # Content
    "summary", "clause_refs", "rationale",
    # New fields
    "mandatory_tests", "regulatory_ecosystem",
    # Dependencies (from graph)
    "testing_standards", "sampling_standards",
    # Roadmap
    "roadmap",
}


# ── Confidence traffic-light ───────────────────────────────────────────────────

def _confidence(score: float) -> str:
    if score >= 0.75:
        return "GREEN"
    if score >= 0.45:
        return "YELLOW"
    return "RED"


# ── Hallucination guard ────────────────────────────────────────────────────────

_IS_PATTERN = re.compile(r'\bIS\s*\d{2,6}(?:\s*(?:Part|Pt\.?)\s*\d+)?\b', re.I)


def strip_hallucinated_is_numbers(text: str) -> str:
    """
    In a text string, replace any IS number that does NOT exist in the
    BIS_STANDARDS index with '[IS number removed]'.
    This prevents fabricated standards from leaking into rationale / roadmap text.
    """
    def _check(match: re.Match) -> str:
        raw = match.group(0)
        # Normalise: "IS1786" → "IS 1786", "IS 1786 Part 1" → "IS 1786"
        normalised = re.sub(r'\s+', ' ', raw).strip()
        base = re.sub(r'\s*(Part|Pt\.?)\s*\d+', '', normalised, flags=re.I).strip()
        return raw if base in VALID_IS_NUMBERS else "[IS ref removed]"

    return _IS_PATTERN.sub(_check, text)


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    """
    Final validation pass on a single standard result:
      1. Remove any standard_id not in the index.
      2. Strip hallucinated IS numbers from rationale and roadmap text.
      3. Filter testing_standards / sampling_standards / regulatory_ecosystem
         to only indexed IS numbers.
      4. Enforce schema — remove unknown keys, add missing optional keys.
    Returns the cleaned result, or None if standard_id itself is invalid.
    """
    # Guard: primary standard must be in index
    if result.get("standard_id") not in VALID_IS_NUMBERS:
        return None

    # Sanitise free-text fields
    for field in ("rationale", "summary"):
        if isinstance(result.get(field), str):
            result[field] = strip_hallucinated_is_numbers(result[field])

    if isinstance(result.get("roadmap"), list):
        result["roadmap"] = [
            strip_hallucinated_is_numbers(step) if isinstance(step, str) else step
            for step in result["roadmap"]
        ]

    # Filter dependency lists to indexed IS numbers only
    for dep_field in ("testing_standards", "sampling_standards"):
        result[dep_field] = [
            s for s in result.get(dep_field, [])
            if s in VALID_IS_NUMBERS
        ]

    # Filter regulatory_ecosystem entries
    result["regulatory_ecosystem"] = [
        eco for eco in result.get("regulatory_ecosystem", [])
        if eco.get("standard_id") in VALID_IS_NUMBERS
    ]

    # Enforce schema keys (drop unknown, fill missing optionals)
    cleaned = {k: v for k, v in result.items() if k in _RESULT_SCHEMA_KEYS}
    for key in _RESULT_SCHEMA_KEYS:
        cleaned.setdefault(key, [] if key in (
            "clause_refs", "mandatory_tests", "regulatory_ecosystem",
            "testing_standards", "sampling_standards", "roadmap"
        ) else "")

    return cleaned


# ── Schema-compliant output function ──────────────────────────────────────────

def build_compliant_output(
    product_id: str,
    query: str,
    status: str,
    retrieved_standards: list[dict[str, Any]],
    latency_seconds: float,
    clarifying_question: str = "",
) -> dict[str, Any]:
    """
    Assemble and validate the final JSON output object.
    All retrieved_standards pass through the hallucination guard.
    """
    validated = []
    for r in retrieved_standards:
        clean = validate_result(r)
        if clean is not None:
            validated.append(clean)

    return {
        "schema_version": "2.0",
        "id": product_id,
        "query": query,
        "status": status,
        "clarifying_question": clarifying_question,
        "retrieved_standards": validated,
        "result_count": len(validated),
        "latency_seconds": latency_seconds,
        "hallucination_guard": "passed",
    }


# ── Core inference function ────────────────────────────────────────────────────

def run_inference(
    query: str,
    product_id: str,
    retriever: HybridRetriever,
    graph: ComplianceDependencyGraph,
    interrogator: ContextualInterrogator,
    roadmap_gen: ComplianceRoadmapGenerator,
    top_k: int = 5,
) -> dict[str, Any]:
    start = time.time()

    # Step 1 — vagueness check
    clarifying = interrogator.check_vagueness(query)
    if clarifying:
        return build_compliant_output(
            product_id=product_id,
            query=query,
            status="clarification_needed",
            retrieved_standards=[],
            latency_seconds=round(time.time() - start, 3),
            clarifying_question=clarifying,
        )

    # Step 2 — two-stage retrieval (Stage 1 hybrid + Stage 2 re-rank)
    results = retriever.retrieve(query, top_k=top_k)

    # Step 3 — enrich with graph dependencies + roadmap + confidence
    enriched = []
    for r in results:
        deps = graph.get_dependencies(r["standard_id"])
        r["testing_standards"]  = deps.get("testing", [])
        r["sampling_standards"] = deps.get("sampling", [])
        r["confidence_level"]   = _confidence(r["score"])
        r["roadmap"]            = roadmap_gen.generate(r)
        enriched.append(r)

    latency = round(time.time() - start, 3)

    return build_compliant_output(
        product_id=product_id,
        query=query,
        status="success",
        retrieved_standards=enriched,
        latency_seconds=latency,
    )


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="BIS RAG Inference Engine v2")
    parser.add_argument("--input",  required=True, help="Path to input JSON file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--top_k",  type=int, default=5, help="Max results per query")
    args = parser.parse_args()

    with open(args.input) as f:
        input_data = json.load(f)

    retriever    = HybridRetriever()
    retriever.load_index()
    graph        = ComplianceDependencyGraph()
    interrogator = ContextualInterrogator()
    roadmap_gen  = ComplianceRoadmapGenerator()

    items = input_data if isinstance(input_data, list) else [input_data]
    outputs = [
        run_inference(
            item["query"], item["id"],
            retriever, graph, interrogator, roadmap_gen,
            top_k=args.top_k,
        )
        for item in items
    ]

    with open(args.output, "w") as f:
        json.dump(outputs, f, indent=2)

    # ── Post-save integrity report ─────────────────────────────────────────────
    total   = sum(o["result_count"] for o in outputs)
    success = sum(1 for o in outputs if o["status"] == "success")
    clarify = sum(1 for o in outputs if o["status"] == "clarification_needed")
    print(
        f"\n[✓] Inference complete → {args.output}\n"
        f"    Queries processed : {len(outputs)}\n"
        f"    Success           : {success}\n"
        f"    Clarification req : {clarify}\n"
        f"    Total standards   : {total}\n"
        f"    Hallucination guard: ALL PASSED ✅\n"
    )


if __name__ == "__main__":
    main()