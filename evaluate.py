"""
evaluate.py — Evaluation: Hit Rate @3, MRR @5, Avg Latency
Usage: python evaluate.py
"""

import time
from retriever import HybridRetriever

# Ground truth test set — (query, expected top standard)
EVAL_SET = [
    ("53 grade OPC cement for prestressed bridge",      "IS 12269"),
    ("ordinary portland cement 43 grade structural",    "IS 8112"),
    ("TMT bar Fe 500 reinforcement seismic zone",       "IS 1786"),
    ("mild steel reinforcement bars concrete",          "IS 432"),
    ("fly ash blended cement sulfate soil",             "IS 1489"),
    ("slag cement underground foundation",              "IS 455"),
    ("sand gravel aggregate for concrete",              "IS 383"),
    ("clay brick red brick wall masonry",               "IS 1077"),
    ("concrete hollow block partition wall",            "IS 2185"),
    ("flat roof bitumen waterproofing",                 "IS 1346"),
    ("waterproofing admixture integral concrete",       "IS 2645"),
    ("cement mortar plastering brickwork",              "IS 2250"),
    ("structural steel plates beams bridges",           "IS 2062"),
    ("gypsum board false ceiling partition drywall",    "IS 2095"),
]

def evaluate():
    retriever = HybridRetriever(alpha=0.5)
    retriever.load_index()

    hit_at_3 = 0
    reciprocal_ranks = []
    latencies = []

    print("\n{'='*60}")
    print("BIS RAG Engine — Evaluation Report")
    print(f"{'='*60}\n")

    for query, expected in EVAL_SET:
        t0 = time.time()
        results = retriever.retrieve(query, top_k=5)
        latency = time.time() - t0
        latencies.append(latency)

        retrieved_ids = [r["standard_id"] for r in results]
        hit3 = expected in retrieved_ids[:3]
        if hit3:
            hit_at_3 += 1

        rr = 0.0
        for rank, std_id in enumerate(retrieved_ids[:5], start=1):
            if std_id == expected:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        status = "✓" if hit3 else "✗"
        print(f"[{status}] Q: {query[:55]:<55} | Expected: {expected:<10} | Got: {retrieved_ids[:3]}")

    n = len(EVAL_SET)
    hit_rate = hit_at_3 / n
    mrr = sum(reciprocal_ranks) / n
    avg_latency = sum(latencies) / n

    print(f"\n{'='*60}")
    print(f"Hit Rate @3  : {hit_rate:.2%}  (Target: >80%)")
    print(f"MRR @5       : {mrr:.3f}   (Target: >0.70)")
    print(f"Avg Latency  : {avg_latency*1000:.1f}ms  (Target: <5000ms)")
    print(f"{'='*60}\n")

    if hit_rate >= 0.80:
        print("✅ Hit Rate @3: PASS")
    else:
        print("❌ Hit Rate @3: FAIL — consider tuning alpha or expanding dataset")

    if mrr >= 0.70:
        print("✅ MRR @5: PASS")
    else:
        print("❌ MRR @5: FAIL")

    if avg_latency < 5.0:
        print("✅ Latency: PASS")
    else:
        print("❌ Latency: FAIL")

if __name__ == "__main__":
    evaluate()
