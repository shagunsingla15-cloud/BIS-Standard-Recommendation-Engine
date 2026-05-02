"""
retriever.py — Two-Stage Hybrid Retrieval + Lightweight Re-Ranker
Stage 1 : BM25 + Dense vector fusion → top-10 candidates
Stage 2 : Rule-based re-ranker (zero-latency, zero-hallucination) → top-k output

Design goals
  • MRR @5 maximisation via re-ranking on specificity signals
  • No external model calls in the hot path (latency stays <10 ms)
  • Rationale now explicitly links a query keyword → BIS clause requirement
  • Mandatory Tests field populated from per-standard test catalogue
  • Regulatory Ecosystem: secondary standards (testing + sampling) surfaced per result
"""

import math
import re
from typing import Any
from collections import Counter
from data.bis_sp21_dataset import BIS_STANDARDS


# ── Mandatory test catalogue (per standard) ────────────────────────────────────
# 2-3 key tests an MSE must perform to prove compliance.

_MANDATORY_TESTS: dict[str, list[str]] = {
    "IS 269":   ["Compressive Strength (3/7/28-day cubes, IS 4031 Pt.6)",
                 "Soundness (Le Chatelier / Autoclave, IS 4031 Pt.3)",
                 "Setting Time (Vicat needle, IS 4031 Pt.5)"],
    "IS 8112":  ["Compressive Strength (3/7/28-day cubes, IS 4031 Pt.6)",
                 "Fineness (Blaine air-permeability, IS 4031 Pt.1)",
                 "Soundness (Le Chatelier, IS 4031 Pt.3)"],
    "IS 12269": ["Compressive Strength (≥53 MPa @ 28 d, IS 4031 Pt.6)",
                 "Chemical Analysis — C₃A content (IS 4032)",
                 "Soundness & Initial Setting Time (IS 4031 Pt.3/5)"],
    "IS 1489":  ["Pozzolanic Activity Index (IS 1727)",
                 "Compressive Strength (IS 4031 Pt.6)",
                 "Soundness (IS 4031 Pt.3)"],
    "IS 455":   ["Slag Content Verification (chemical, IS 4032)",
                 "Compressive Strength (IS 4031 Pt.6)",
                 "Soundness (IS 4031 Pt.3)"],
    "IS 432":   ["Tensile Strength & Yield Stress (IS 1608)",
                 "Bend Test (IS 1599)",
                 "Dimensional Check — diameter & mass (IS 1732)"],
    "IS 1786":  ["Tensile Strength & 0.2% Proof Stress (IS 1608)",
                 "Bend / Re-bend Test (IS 1599)",
                 "Chemical Analysis — Carbon & Sulphur (IS 228)"],
    "IS 2062":  ["Tensile Strength & Yield Strength (IS 1608)",
                 "Charpy Impact Test (IS 1499)",
                 "Chemical Composition — Carbon equivalent (IS 228)"],
    "IS 383":   ["Sieve Analysis / Grading (IS 2386 Pt.1)",
                 "Silt Content — field settling test (IS 2386 Pt.2)",
                 "Aggregate Impact / Crushing Value (IS 2386 Pt.4)"],
    "IS 2645":  ["Water Absorption Reduction Test (IS 4031 Pt.6 modified)",
                 "Compressive Strength of waterproofed mortar (IS 4031 Pt.6)",
                 "Permeability Test (IS 3085)"],
    "IS 1346":  ["Peel Strength of bitumen felt (IS 1322)",
                 "Softening Point of bitumen binder (IS 1205)",
                 "Water Impermeability Test (IS 1322 Pt.3)"],
    "IS 1077":  ["Compressive Strength of bricks (IS 3495 Pt.1)",
                 "Water Absorption (IS 3495 Pt.2)",
                 "Efflorescence Rating (IS 3495 Pt.3)"],
    "IS 2185":  ["Compressive Strength of concrete block (IS 2185 Annex B)",
                 "Water Absorption (IS 2185 Annex C)",
                 "Block Dimensions — length/width/height (IS 2185 Cl.6)"],
    "IS 2095":  ["Flexural Strength — dry & wet (IS 2542)",
                 "Moisture Resistance Classification (IS 2095 Cl.7)",
                 "Dimensional Tolerance (IS 2095 Cl.6)"],
    "IS 2250":  ["Compressive Strength of mortar cubes (IS 2250 Annex A)",
                 "Water Retention test (IS 2250 Annex B)",
                 "Flow Table Consistency (IS 5512)"],
    "IS 516":   ["Cube / Cylinder compressive strength (IS 516 Cl.5)",
                 "Flexural Strength — two-point loading (IS 516 Cl.6)",
                 "Splitting Tensile Strength (IS 516 Cl.7)"],
    "IS 2386":  ["Particle Size Analysis — sieve test (IS 2386 Pt.1)",
                 "Flakiness & Elongation Index (IS 2386 Pt.1)",
                 "Water Absorption & Specific Gravity (IS 2386 Pt.3)"],
    "IS 4031":  ["Fineness — Blaine / 90-μm sieve (IS 4031 Pt.1/2)",
                 "Vicat Setting Time (IS 4031 Pt.5)",
                 "Compressive Strength of cement mortar (IS 4031 Pt.6)"],
    "IS 3535":  ["Lot Identification & Sample size verification (IS 3535 Cl.4)",
                 "Composite sample preparation (IS 3535 Cl.5)"],
    "IS 3025":  ["pH & Turbidity (IS 3025 Pt.11/10)",
                 "Chloride Content (IS 3025 Pt.32)",
                 "Sulphate Content (IS 3025 Pt.24)"],
}

# Secondary standards to surface in the Regulatory Ecosystem field
# Derived from the dataset's testing_deps / sampling_deps; we add
# human-readable descriptions here for richer output.

_SECONDARY_STD_META: dict[str, dict[str, str]] = {
    "IS 4031":  {"role": "Testing",  "desc": "Physical tests for hydraulic cement"},
    "IS 3535":  {"role": "Sampling", "desc": "Sampling of hydraulic cements"},
    "IS 1608":  {"role": "Testing",  "desc": "Tensile testing of metals"},
    "IS 1599":  {"role": "Testing",  "desc": "Bend test for steel"},
    "IS 4711":  {"role": "Sampling", "desc": "Sampling of steel"},
    "IS 2386":  {"role": "Testing",  "desc": "Tests for concrete aggregates"},
    "IS 2430":  {"role": "Sampling", "desc": "Sampling of aggregates"},
    "IS 1727":  {"role": "Testing",  "desc": "Pozzolanic activity tests"},
    "IS 650":   {"role": "Testing",  "desc": "Standard sand for cement testing"},
    "IS 1322":  {"role": "Testing",  "desc": "Bitumen felt testing"},
    "IS 3495":  {"role": "Testing",  "desc": "Tests for clay building bricks"},
    "IS 5454":  {"role": "Sampling", "desc": "Sampling of clay bricks"},
    "IS 4905":  {"role": "Sampling", "desc": "Sampling of masonry units"},
    "IS 2542":  {"role": "Testing",  "desc": "Tests for gypsum plaster products"},
    "IS 1199":  {"role": "Sampling", "desc": "Sampling fresh concrete"},
}


# ── Valid IS numbers in the index (hallucination guard) ───────────────────────

VALID_IS_NUMBERS: frozenset[str] = frozenset(
    std["standard_id"] for std in BIS_STANDARDS
)


# ═══════════════════════════════════════════════════════════════════════════════
# BM25
# ═══════════════════════════════════════════════════════════════════════════════

class BM25:
    """Lightweight BM25 — no external dependencies."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_freqs: list[Counter] = []
        self.idf: dict[str, float] = {}
        self.avgdl: float = 0.0

    def fit(self, corpus: list[list[str]]) -> None:
        self.corpus = corpus
        self.avgdl = sum(len(d) for d in corpus) / max(len(corpus), 1)
        df: Counter = Counter()
        for doc in corpus:
            for term in set(doc):
                df[term] += 1
        N = len(corpus)
        self.idf = {
            t: math.log((N - f + 0.5) / (f + 0.5) + 1)
            for t, f in df.items()
        }
        self.doc_freqs = [Counter(doc) for doc in corpus]

    def get_scores(self, query_terms: list[str]) -> list[float]:
        scores = []
        for i, doc in enumerate(self.corpus):
            dl = len(doc)
            freq_map = self.doc_freqs[i]
            s = 0.0
            for term in query_terms:
                if term not in self.idf:
                    continue
                tf = freq_map.get(term, 0)
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                s += self.idf[term] * (num / den)
            scores.append(s)
        return scores


# ═══════════════════════════════════════════════════════════════════════════════
# Dense (TF-IDF cosine proxy)
# ═══════════════════════════════════════════════════════════════════════════════

class DenseRetriever:
    """TF-IDF cosine similarity — semantic proxy without GPU."""

    def __init__(self):
        self.idf: dict[str, float] = {}
        self.doc_vectors: list[dict[str, float]] = []

    @staticmethod
    def _tok(text: str) -> list[str]:
        return re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())

    def _tfidf(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        return {t: (c / total) * self.idf.get(t, 0) for t, c in tf.items()}

    @staticmethod
    def _cos(a: dict, b: dict) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[k] * b[k] for k in common)
        na = math.sqrt(sum(v ** 2 for v in a.values()))
        nb = math.sqrt(sum(v ** 2 for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def fit(self, documents: list[str]) -> None:
        tokenized = [self._tok(d) for d in documents]
        N = len(tokenized)
        df: Counter = Counter()
        for doc in tokenized:
            for t in set(doc):
                df[t] += 1
        self.idf = {t: math.log((N + 1) / (f + 1)) + 1 for t, f in df.items()}
        self.doc_vectors = [self._tfidf(tok) for tok in tokenized]

    def get_scores(self, query: str) -> list[float]:
        q_vec = self._tfidf(self._tok(query))
        return [self._cos(q_vec, dv) for dv in self.doc_vectors]


# ═══════════════════════════════════════════════════════════════════════════════
# Lightweight Re-Ranker  (Stage 2)
# ═══════════════════════════════════════════════════════════════════════════════

class LightweightReRanker:
    """
    Rule-based re-ranker that runs on the top-10 Stage-1 candidates.

    Scoring signals (additive):
      +0.30  exact IS number match in query
      +0.20  grade / product code match (Fe 500, 53 grade, E350 …)
      +0.15  application context match (seismic, marine, coastal, RCC …)
      +0.10  per matched keyword beyond the first (capped at 3 extra)
      −0.15  category mismatch (e.g. cement standard for steel query)
    """

    _GRADE_TOKENS = re.compile(
        r'\b(fe\s*\d{3}d?|e\s*\d{3}|\d{2,3}\s*grade|opc|ppc|psc|m\d{2}|'
        r'53|43|33|415|500|550|600|e250|e350|e410)\b',
        re.I
    )
    _APP_TOKENS = re.compile(
        r'\b(seismic|marine|coastal|bridge|basement|rcc|pcc|prestressed|'
        r'underground|sulfate|high.?rise|flat.?roof|load.?bearing|partition)\b',
        re.I
    )
    _CATEGORY_WORDS: dict[str, list[str]] = {
        "Steel":       ["steel", "tmt", "rebar", "bar", "reinforcement", "rod"],
        "Cement":      ["cement", "opc", "ppc", "psc", "portland", "clinker"],
        "Aggregates":  ["aggregate", "sand", "gravel", "crushed stone"],
        "Waterproofing": ["waterproof", "bitumen", "membrane", "felt"],
        "Masonry":     ["brick", "block", "mortar", "masonry"],
        "Finishing":   ["gypsum", "plaster", "drywall", "partition board"],
        "Testing":     ["test", "testing", "strength test", "cube test"],
        "Sampling":    ["sampling", "sample", "lot"],
    }

    def _query_category(self, query: str) -> str | None:
        q = query.lower()
        for cat, words in self._CATEGORY_WORDS.items():
            if any(w in q for w in words):
                return cat
        return None

    def rerank(self, query: str, candidates: list[dict[str, Any]],
               final_k: int = 5) -> list[dict[str, Any]]:
        q = query.lower()
        q_cat = self._query_category(query)
        q_grades = set(self._GRADE_TOKENS.findall(q))
        q_apps   = set(self._APP_TOKENS.findall(q))

        scored = []
        for cand in candidates:
            boost = 0.0
            std_id = cand["standard_id"].lower()

            # Exact IS number in query
            if std_id in q:
                boost += 0.30

            # Grade token overlap
            std_text = (
                cand["title"] + " " +
                cand["summary"] + " " +
                " ".join(cand["keywords"])
            ).lower()
            grade_hits = set(self._GRADE_TOKENS.findall(std_text)) & q_grades
            if grade_hits:
                boost += 0.20

            # Application context overlap
            app_hits = set(self._APP_TOKENS.findall(std_text)) & q_apps
            if app_hits:
                boost += 0.15

            # Extra keyword hits (beyond baseline already in Stage-1 score)
            kw_hits = sum(1 for kw in cand["keywords"] if kw.lower() in q)
            boost += min(kw_hits - 1, 3) * 0.10 if kw_hits > 1 else 0.0

            # Category mismatch penalty
            if q_cat and cand["category"] != q_cat and cand["category"] not in ("Testing", "Sampling"):
                boost -= 0.15

            cand = dict(cand)               # shallow copy — don't mutate original
            cand["rerank_boost"] = round(boost, 4)
            cand["final_score"]  = round(cand["score"] + boost, 4)
            scored.append(cand)

        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored[:final_k]


# ═══════════════════════════════════════════════════════════════════════════════
# Rationale generator
# ═══════════════════════════════════════════════════════════════════════════════

def build_rationale(query: str, std: dict[str, Any]) -> str:
    """
    Construct a rationale that explicitly links a keyword from the user query
    to a specific BIS clause requirement — never generic filler.
    """
    q_lower = query.lower()

    # Find matched keywords (query → standard keyword list)
    matched_kw = [kw for kw in std["keywords"] if kw.lower() in q_lower]

    # Find matched clause refs whose text overlaps with query terms
    q_tokens = set(re.findall(r'\b[a-zA-Z0-9]+\b', q_lower))
    matched_clauses = [
        cl for cl in std.get("clause_refs", [])
        if any(tok in cl.lower() for tok in q_tokens)
    ] or std.get("clause_refs", [])[:1]   # fallback: first clause

    kw_part = (
        f"your query specifies '{matched_kw[0]}'"
        if matched_kw
        else f"semantic context of your query"
    )
    clause_part = (
        f"{matched_clauses[0]}" if matched_clauses else "the specification clauses"
    )
    std_id = std["standard_id"]
    title  = std["title"]

    # Append application-specific reasoning
    app_notes = []
    if any(w in q_lower for w in ("seismic", "earthquake", "zone iv", "zone v")):
        app_notes.append("seismic applications require Fe 500D with enhanced ductility per Annex F")
    if any(w in q_lower for w in ("marine", "coastal", "chloride", "sea")):
        app_notes.append("marine exposure mandates low C₃A cement and low w/c ratio per IS 456 Table 5")
    if any(w in q_lower for w in ("bridge", "prestressed", "high rise", "flyover")):
        app_notes.append("high-strength concrete structures require 53-grade or blended cement with w/c ≤ 0.40")
    if any(w in q_lower for w in ("sulfate", "sulphate", "aggressive soil")):
        app_notes.append("sulfate-bearing ground mandates PSC or PPC to limit C₃A dissolution")

    rationale = (
        f"Because {kw_part}, {std_id} ({title}) is directly applicable: "
        f"{clause_part} governs the performance requirements for this use case."
    )
    if app_notes:
        rationale += f" Note: {app_notes[0].capitalize()}."

    return rationale


# ═══════════════════════════════════════════════════════════════════════════════
# Regulatory Ecosystem builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_regulatory_ecosystem(std: dict[str, Any]) -> list[dict[str, str]]:
    """
    For a primary product standard, surface 1-2 secondary standards
    (testing methods or sampling procedures) with role labels.
    Only returns IS numbers that exist in the index (hallucination guard).
    """
    ecosystem = []
    seen: set[str] = set()

    for dep_is in std.get("testing_deps", []) + std.get("sampling_deps", []):
        if dep_is in seen or dep_is not in VALID_IS_NUMBERS:
            continue
        seen.add(dep_is)
        meta = _SECONDARY_STD_META.get(dep_is, {})
        ecosystem.append({
            "standard_id": dep_is,
            "role":        meta.get("role", "Testing"),
            "description": meta.get("desc", "Related standard"),
        })
        if len(ecosystem) >= 2:
            break

    return ecosystem


# ═══════════════════════════════════════════════════════════════════════════════
# HybridRetriever  (two-stage, drop-in replacement)
# ═══════════════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """
    Stage 1: BM25 + Dense fusion → top-10 candidates.
    Stage 2: LightweightReRanker → top-k final results.

    Public API is identical to the original HybridRetriever.
    """

    STAGE1_K = 10   # candidates fed to re-ranker

    def __init__(self, alpha: float = 0.5):
        self.alpha   = alpha
        self.bm25    = BM25()
        self.dense   = DenseRetriever()
        self.reranker = LightweightReRanker()
        self.standards = BIS_STANDARDS
        self._indexed  = False

    # ── Index ──────────────────────────────────────────────────────────────────

    def load_index(self) -> None:
        bm25_corpus, dense_corpus = [], []
        for std in self.standards:
            tokens = (
                re.findall(r'\b[a-zA-Z0-9]+\b', std["title"].lower()) +
                std["keywords"] +
                re.findall(r'\b[a-zA-Z0-9]+\b', std["summary"].lower())
            )
            bm25_corpus.append(tokens)
            dense_corpus.append(
                f"{std['title']} {std['summary']} {' '.join(std['keywords'])}"
            )
        self.bm25.fit(bm25_corpus)
        self.dense.fit(dense_corpus)
        self._indexed = True
        print(f"[✓] Index built — {len(self.standards)} standards, "
              f"2-stage retrieval enabled.")

    # ── Retrieval ──────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self._indexed:
            self.load_index()

        q_tokens = re.findall(r'\b[a-zA-Z0-9]+\b', query.lower())

        # ── Stage 1: hybrid fusion ─────────────────────────────────────────────
        bm25_raw   = self.bm25.get_scores(q_tokens)
        dense_raw  = self.dense.get_scores(query)

        def _norm(scores: list[float]) -> list[float]:
            mx = max(scores) if max(scores) > 0 else 1.0
            return [s / mx for s in scores]

        bm25_n  = _norm(bm25_raw)
        dense_n = _norm(dense_raw)
        hybrid  = [
            self.alpha * bm25_n[i] + (1 - self.alpha) * dense_n[i]
            for i in range(len(self.standards))
        ]

        stage1_ranked = sorted(
            enumerate(hybrid), key=lambda x: x[1], reverse=True
        )[:self.STAGE1_K]

        # Assemble candidate dicts for re-ranker
        candidates: list[dict[str, Any]] = []
        for idx, score in stage1_ranked:
            if score < 0.05:
                continue
            std = self.standards[idx]
            candidates.append({
                **std,                           # spread all dataset fields
                "score":       round(score, 4),
                "bm25_score":  round(bm25_n[idx], 4),
                "dense_score": round(dense_n[idx], 4),
            })

        # ── Stage 2: re-rank → top-k ───────────────────────────────────────────
        reranked = self.reranker.rerank(query, candidates, final_k=top_k)

        # ── Enrich each result ─────────────────────────────────────────────────
        results = []
        for r in reranked:
            std_dict = {k: v for k, v in r.items()
                        if k not in ("score", "bm25_score", "dense_score",
                                     "rerank_boost", "final_score")}
            results.append({
                "standard_id":         r["standard_id"],
                "title":               r["title"],
                "category":            r["category"],
                "summary":             r["summary"],
                "clause_refs":         r.get("clause_refs", []),
                "score":               r["final_score"],
                "bm25_score":          r["bm25_score"],
                "dense_score":         r["dense_score"],
                "rerank_boost":        r["rerank_boost"],
                "rationale":           build_rationale(query, r),
                "mandatory_tests":     _MANDATORY_TESTS.get(r["standard_id"], []),
                "regulatory_ecosystem": build_regulatory_ecosystem(r),
            })

        return results