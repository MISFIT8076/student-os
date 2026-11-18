"""Study-material assistant — ask questions over your own notes (RAG).

A lightweight, dependency-free retrieval layer: TF-IDF vectors + cosine
similarity (numpy) over passages split from the student's notes. Returns the
most relevant passages; if an LLM key is configured, it can compose a short
answer grounded in them (otherwise the passages ARE the answer — extractive, so
it never hallucinates).

Kept simple and inspectable for the report; swap TF-IDF for embeddings later
without touching the callers.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np

from app.config import BACKEND_ROOT, get_settings

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class RagIndex:
    """TF-IDF index over a list of passages."""

    def __init__(self) -> None:
        self.passages: list[dict] = []
        self._vocab: dict[str, int] = {}
        self._idf: np.ndarray | None = None
        self._matrix: np.ndarray | None = None

    def fit(self, passages: list[dict]) -> "RagIndex":
        """passages: [{'source': str, 'text': str}, ...]"""
        self.passages = passages
        docs_tokens = [_tokenize(p["text"]) for p in passages]
        vocab = sorted({tok for toks in docs_tokens for tok in toks})
        self._vocab = {t: i for i, t in enumerate(vocab)}
        n = len(passages)
        v = len(vocab)
        if n == 0 or v == 0:
            self._matrix = np.zeros((n, v))
            self._idf = np.ones(v)
            return self

        df = np.zeros(v)
        tf = np.zeros((n, v))
        for i, toks in enumerate(docs_tokens):
            for tok in toks:
                tf[i, self._vocab[tok]] += 1
            if toks:
                tf[i] /= len(toks)
            for tok in set(toks):
                df[self._vocab[tok]] += 1
        self._idf = np.log((1 + n) / (1 + df)) + 1.0
        self._matrix = _l2(tf * self._idf)
        return self

    def _vectorize(self, text: str) -> np.ndarray:
        vec = np.zeros(len(self._vocab))
        toks = _tokenize(text)
        for tok in toks:
            j = self._vocab.get(tok)
            if j is not None:
                vec[j] += 1
        if toks:
            vec /= len(toks)
        return _l2((vec * self._idf).reshape(1, -1))[0]

    def query(self, question: str, k: int = 3) -> list[dict]:
        if self._matrix is None or len(self.passages) == 0:
            return []
        q = self._vectorize(question)
        scores = self._matrix @ q
        order = np.argsort(-scores)[:k]
        results = []
        for idx in order:
            if scores[idx] <= 0:
                continue
            p = self.passages[int(idx)]
            results.append({"source": p["source"], "text": p["text"],
                            "score": round(float(scores[idx]), 3)})
        return results


def _l2(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


def load_corpus(notes_dir: Path | None = None) -> list[dict]:
    """Split note files (.md/.txt) into passages on blank lines."""
    notes_dir = Path(notes_dir or get_settings().resolved_study_notes_dir)
    passages: list[dict] = []
    if not notes_dir.exists():
        return passages
    for path in sorted(notes_dir.glob("**/*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        for chunk in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
            text = chunk.strip()
            if len(text) >= 30:  # skip tiny fragments/headers
                passages.append({"source": path.name, "text": text})
    return passages


def answer(question: str, notes_dir: Path | None = None, k: int = 3) -> dict:
    """Retrieve the top passages for a question (grounded, extractive)."""
    passages = load_corpus(notes_dir)
    hits = RagIndex().fit(passages).query(question, k)
    return {
        "question": question,
        "answer": hits[0]["text"] if hits else "No relevant notes found.",
        "passages": hits,
        "indexed_passages": len(passages),
    }


DEFAULT_NOTES_DIR = BACKEND_ROOT / "eval" / "rag_corpus"
