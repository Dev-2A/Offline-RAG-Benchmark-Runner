from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SearchHit:
    doc_id: str
    label: str
    score: float


class SearchBackend(Protocol):
    def search(self, query_vector: list[float], topn: int) -> list[SearchHit]: ...
