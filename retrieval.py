"""A small, self-contained retriever over the local runbook + incident corpus.

Uses scikit-learn's TF-IDF rather than embeddings deliberately: it requires no model
download and no network call, so `pip install -r requirements.txt && python demo.py`
works completely offline. In a production system this interface would be backed by
Amazon Bedrock Knowledge Bases or a managed vector store (Pinecone, OpenSearch) instead;
see the companion `rag-pipeline-pinecone` repo for that pattern. Swapping the backend
here means implementing this same `Retriever` interface against a different store; it
does not require changing any of the agent code that calls it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .state import RetrievedDoc

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class _Doc:
    doc_id: str
    doc_type: str
    title: str
    text: str


def _load_runbooks() -> List[_Doc]:
    docs = []
    for path in sorted((DATA_DIR / "runbooks").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # crude front-matter parse, good enough for this synthetic corpus
        doc_id = path.stem.split("-")[0] + "-" + path.stem.split("-")[1]
        title_line = next((l for l in text.splitlines() if l.startswith("title:")), "")
        title = title_line.replace("title:", "").strip() or path.stem
        docs.append(_Doc(doc_id=doc_id, doc_type="runbook", title=title, text=text))
    return docs


def _load_incidents() -> List[_Doc]:
    path = DATA_DIR / "incidents" / "sample_incidents.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    docs = []
    for item in items:
        text = f"{item['title']}\n{item['summary']}\n{item['lesson']}"
        docs.append(
            _Doc(doc_id=item["id"], doc_type="incident", title=item["title"], text=text)
        )
    return docs


class Retriever:
    def __init__(self) -> None:
        self._docs = _load_runbooks() + _load_incidents()
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform([d.text for d in self._docs])

    def search(self, query: str, top_k: int = 3) -> List[RetrievedDoc]:
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        ranked = sorted(
            zip(self._docs, scores), key=lambda pair: pair[1], reverse=True
        )[:top_k]
        return [
            RetrievedDoc(
                doc_id=doc.doc_id,
                doc_type=doc.doc_type,
                title=doc.title,
                score=round(float(score), 3),
                text=doc.text,
            )
            for doc, score in ranked
            if score > 0
        ]


_default_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = Retriever()
    return _default_retriever
