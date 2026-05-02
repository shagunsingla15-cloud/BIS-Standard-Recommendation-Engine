"""
parent_doc_retriever.py — Parent-Document Retrieval Strategy
Maintains full technical context by storing parent docs and retrieving child chunks,
then returning the full parent for LLM context.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ChildChunk:
    """A small, searchable chunk derived from a parent document."""
    chunk_id: str
    parent_id: str
    text: str
    chunk_type: str  # 'clause', 'summary', 'keyword_block'
    tokens: List[str] = field(default_factory=list)


@dataclass
class ParentDocument:
    """Full BIS standard document — preserved for LLM context."""
    doc_id: str
    standard_id: str
    title: str
    category: str
    full_text: str
    clauses: Dict[str, str] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


class ParentDocumentRetriever:
    """
    Strategy:
      - Index small child chunks (clause-level, ~100-200 tokens) for precise retrieval
      - When a child chunk matches, return its full parent document to the LLM
      - Prevents context loss from over-chunking of technical standards
    """

    def __init__(self, chunk_size: int = 150, overlap: int = 20):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.parent_store: Dict[str, ParentDocument] = {}
        self.child_chunks: List[ChildChunk] = []

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z0-9/.:]+\b', text.lower())

    def _chunk_text(self, text: str, doc_id: str) -> List[ChildChunk]:
        """Chunk text into overlapping windows, preserving clause boundaries."""
        chunks = []
        # First, split on clause markers
        clause_pattern = re.compile(r'(Cl\.\s*\d+[\.\d]*|Clause\s+\d+)', re.IGNORECASE)
        parts = clause_pattern.split(text)

        current_clause = "General"
        for i, part in enumerate(parts):
            if clause_pattern.match(part):
                current_clause = part.strip()
                continue
            if not part.strip():
                continue
            # Sliding window within each clause part
            tokens = self._tokenize(part)
            start = 0
            chunk_idx = 0
            while start < len(tokens):
                end = min(start + self.chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]
                chunk_id = f"{doc_id}_{current_clause}_chunk{chunk_idx}"
                chunks.append(ChildChunk(
                    chunk_id=chunk_id,
                    parent_id=doc_id,
                    text=" ".join(chunk_tokens),
                    chunk_type="clause",
                    tokens=chunk_tokens
                ))
                start += self.chunk_size - self.overlap
                chunk_idx += 1
        return chunks

    def add_document(self, standard: Dict):
        """Ingest a BIS standard as parent + derived child chunks."""
        doc_id = standard["standard_id"].replace(" ", "_")

        # Build full text for parent
        full_text = (
            f"{standard['standard_id']}: {standard['title']}\n"
            f"Category: {standard['category']}\n"
            f"Summary: {standard['summary']}\n"
            f"Keywords: {', '.join(standard['keywords'])}\n"
            f"Clauses: {', '.join(standard['clause_refs'])}\n"
        )

        parent = ParentDocument(
            doc_id=doc_id,
            standard_id=standard["standard_id"],
            title=standard["title"],
            category=standard["category"],
            full_text=full_text,
            clauses={ref: "" for ref in standard["clause_refs"]},
            metadata={
                "testing_deps": standard.get("testing_deps", []),
                "sampling_deps": standard.get("sampling_deps", [])
            }
        )
        self.parent_store[doc_id] = parent

        # Create child chunks from summary + keywords (searchable units)
        summary_chunk = ChildChunk(
            chunk_id=f"{doc_id}_summary",
            parent_id=doc_id,
            text=standard["summary"],
            chunk_type="summary",
            tokens=self._tokenize(standard["summary"])
        )
        self.child_chunks.append(summary_chunk)

        keyword_chunk = ChildChunk(
            chunk_id=f"{doc_id}_keywords",
            parent_id=doc_id,
            text=" ".join(standard["keywords"]),
            chunk_type="keyword_block",
            tokens=[kw.lower() for kw in standard["keywords"]]
        )
        self.child_chunks.append(keyword_chunk)

        # Clause-level chunks from full text
        clause_chunks = self._chunk_text(full_text, doc_id)
        self.child_chunks.extend(clause_chunks)

    def build_index(self, standards: List[Dict]):
        """Build parent store and child chunk index from all standards."""
        for std in standards:
            self.add_document(std)
        print(
            f"[✓] ParentDocumentRetriever: {len(self.parent_store)} parents, "
            f"{len(self.child_chunks)} child chunks indexed."
        )

    def search_chunks(self, query: str, top_k: int = 10) -> List[ChildChunk]:
        """Simple token-overlap search on child chunks."""
        query_tokens = set(self._tokenize(query))
        scored = []
        for chunk in self.child_chunks:
            overlap = len(query_tokens & set(chunk.tokens))
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def retrieve_parents(self, query: str, top_k: int = 5) -> List[ParentDocument]:
        """
        Retrieve child chunks, then return UNIQUE parent documents.
        This is the core Parent-Document Retrieval pattern.
        """
        matched_chunks = self.search_chunks(query, top_k=top_k * 3)

        # Deduplicate by parent, preserving order
        seen_parents = set()
        parents = []
        for chunk in matched_chunks:
            pid = chunk.parent_id
            if pid not in seen_parents:
                seen_parents.add(pid)
                parent = self.parent_store.get(pid)
                if parent:
                    parents.append(parent)
            if len(parents) >= top_k:
                break
        return parents

    def get_full_context(self, parent: ParentDocument) -> str:
        """Return complete document text for LLM prompt context."""
        return parent.full_text


# Demo usage
if __name__ == "__main__":
    from data.bis_sp21_dataset import BIS_STANDARDS
    pdr = ParentDocumentRetriever(chunk_size=100, overlap=15)
    pdr.build_index(BIS_STANDARDS)

    query = "high strength cement for marine bridge construction"
    parents = pdr.retrieve_parents(query, top_k=3)
    print(f"\nQuery: {query}")
    print(f"Top {len(parents)} parent documents retrieved:")
    for p in parents:
        print(f"  → {p.standard_id}: {p.title}")
