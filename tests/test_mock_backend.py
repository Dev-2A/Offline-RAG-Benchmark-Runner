import json
import os
import tempfile

from obrbr.config import EmbeddingCfg, IndexCfg
from obrbr.search.mock_backend import MockBackend


def test_mock_backend_search_runs():
    with tempfile.TemporaryDirectory() as td:
        docs_path = os.path.join(td, "docs.jsonl")
        docs = [
            {"doc_id": "d1", "answer_id": "a1", "question": "hello world"},
            {"doc_id": "d2", "answer_id": "a2", "question": "bye world"},
        ]
        with open(docs_path, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

        idx = IndexCfg(
            name="test",
            backend="mock",
            vector_field="question_vt",
            docs_path=docs_path,
            doc_vector=EmbeddingCfg(provider="local_hash", dim=16, salt="A"),
        )

        backend = MockBackend(idx)
        qvec = [0.0] * 16
        # If qvec is zero, dot-product will be 0 for all; still should not crash.
        hits = backend.search(qvec, topn=2)
        assert len(hits) == 2
