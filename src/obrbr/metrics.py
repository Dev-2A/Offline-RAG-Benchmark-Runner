from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set


@dataclass
class QueryEval:
    query_id: str
    truth: Set[str]
    ranked_labels: List[str]    # labels/doc-ids used for hit checking


def recall_at_k(evals: Sequence[QueryEval], k: int) -> float:
    if not evals:
        return 0.0
    hit = 0
    for e in evals:
        topk = e.ranked_labels[:k]
        if any(x in e.truth for x in topk):
            hit += 1
    return hit / len(evals)


def recall_table(evals: Sequence[QueryEval], k_list: Iterable[int]) -> Dict[int, float]:
    return {k: recall_at_k(evals, k) for k in k_list}