from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from ..config import IndexCfg
from ..embedder import Embedder, local_hash_embed
from .backend_base import SearchHit


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass
class MockBackend:
    idx_cfg: IndexCfg
    
    def __post_init__(self) -> None:
        if not self.idx_cfg.docs_path:
            raise ValueError(f"[{self.idx_cfg.name}] docs_path is required for mock backend")
        
        with open(self.idx_cfg.docs_path, "r", encoding="utf-8") as f:
            self.docs = [json.loads(line) for line in f if line.strip()]
        
        # Build document vectors in-memory (acts like "stored vector field")
        dv = self.idx_cfg.doc_vector
        if dv is None:
            from ..config import EmbeddingCfg
            dv = EmbeddingCfg(provider="local_hash", dim=32, salt="A")

        doc_embedder = Embedder(dv)
        self.doc_vectors: List[List[float]] = []
        for d in self.docs:
            text = str(d.get(self.idx_cfg.doc_text_field, ""))
            vec = doc_embedder.embed(text)
            d[self.idx_cfg.vector_field] = vec
            self.doc_vectors.append(vec)
    
    def search(self, query_vector: List[float], topn: int) -> List[SearchHit]:
        scored: List[SearchHit] = []
        for d, v in zip(self.docs, self.doc_vectors):
            score = _dot(query_vector, v)   # cosine since both normalized
            scored.append(
                SearchHit(
                    doc_id=str(d.get(self.idx_cfg.id_field, "")),
                    label=str(d.get(self.idx_cfg.label_field, "")),
                    score=float(score),
                )
            )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:topn]