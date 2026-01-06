from __future__ import annotations

from dataclasses import dataclass

import requests

from ..config import IndexCfg
from .backend_base import SearchHit


@dataclass
class ElasticsearchBackend:
    idx_cfg: IndexCfg

    def _auth(self) -> tuple[str, str] | None:
        if self.idx_cfg.es_auth_user and self.idx_cfg.es_auth_pass:
            return (self.idx_cfg.es_auth_user, self.idx_cfg.es_auth_pass)
        return None

    def search(self, query_vector: list[float], topn: int) -> list[SearchHit]:
        """
        Minimal ES search.
        - If es_use_knn: uses knn query (ES 8+)
        - else: uses script_score cosineSimilarity (requires dense_vector)
        """
        if not self.idx_cfg.es_url or not self.idx_cfg.es_index:
            raise ValueError(
                f"[{self.idx_cfg.name}] es_url/es_index are required for elasticsearch backend"
            )

        url = self.idx_cfg.es_url.rstrip("/") + f"/{self.idx_cfg.es_index}/_search"
        headers = {"Content-Type": "application/json"}

        if self.idx_cfg.es_use_knn:
            body = {
                "size": topn,
                "knn": {
                    "field": self.idx_cfg.vector_field,
                    "query_vector": query_vector,
                    "k": topn,
                    "num_candidates": max(50, topn * 10),
                },
                "_source": [self.idx_cfg.label_field],
            }
        else:
            body = {
                "size": topn,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": f"cosineSimilarity(params.q, '{self.idx_cfg.vector_field}')",
                            "params": {"q": query_vector},
                        },
                    }
                },
                "_source": [self.idx_cfg.label_field],
            }

        r = requests.post(
            url,
            json=body,
            headers=headers,
            auth=self._auth(),
            verify=self.idx_cfg.es_verify_tls,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        out: list[SearchHit] = []
        for h in hits:
            doc_id = str(h.get("_id", ""))
            score = float(h.get("_score", 0.0))
            src = h.get("_source", {}) or {}
            label = str(src.get(self.idx_cfg.label_field, ""))
            out.append(SearchHit(doc_id=doc_id, label=label, score=score))
        return out
