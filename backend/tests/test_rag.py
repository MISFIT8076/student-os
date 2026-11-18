"""Tests for the study-material RAG retrieval."""
from __future__ import annotations

from app.intelligence.rag import RagIndex, answer

DOCS = [
    {"source": "os.md", "text": "Paging divides memory into fixed-size frames and pages; the page table maps pages to frames."},
    {"source": "os.md", "text": "Round-robin scheduling gives each process a fixed time quantum for fairness and responsiveness."},
    {"source": "dbms.md", "text": "ACID means atomicity, consistency, isolation, and durability for reliable transactions."},
]


def test_retrieves_most_relevant_passage():
    idx = RagIndex().fit(DOCS)
    hits = idx.query("what is paging in memory management?", k=1)
    assert hits and "Paging" in hits[0]["text"]


def test_scheduling_query_matches_scheduling_passage():
    idx = RagIndex().fit(DOCS)
    hits = idx.query("how does round robin scheduling work", k=1)
    assert hits and "Round-robin" in hits[0]["text"]


def test_empty_index_returns_no_hits():
    assert RagIndex().fit([]).query("anything") == []


def test_answer_over_sample_corpus():
    # Uses the bundled eval/rag_corpus notes.
    res = answer("explain ACID properties", k=2)
    assert res["indexed_passages"] > 0
    assert "atomicity" in res["answer"].lower() or any(
        "atomicity" in p["text"].lower() for p in res["passages"]
    )
