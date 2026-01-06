from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class EmbeddingCfg:
    provider: str
    dim: int
    salt: str = ""
    base_url: str = ""
    endpoint_path: str = "/embed"
    timeout_sec: int = 15


@dataclass
class ModelCfg:
    name: str
    query_embedding: EmbeddingCfg


@dataclass
class IndexCfg:
    name: str
    backend: str  # mock / elasticsearch
    vector_field: str
    docs_path: str = ""
    id_field: str = "doc_id"
    label_field: str = "answer_id"
    doc_text_field = str = "question"
    doc_vector: EmbeddingCfg | None = None

    # elasticsearch options (optional)
    es_url: str = ""
    es_index: str = ""
    es_auth_user: str = ""
    es_auth_pass: str = ""
    es_verify_tls: bool = True
    es_use_knn: bool = True


@dataclass
class RunCfg:
    output_root: str
    k_list: list[int]
    topn: int = 10
    fail_fast: bool = False


@dataclass
class DataCfg:
    queries_path: str
    truth_key: str = "answer_ids"


@dataclass
class BenchCfg:
    project_name: str
    run: RunCfg
    data: DataCfg
    models: dict[str, ModelCfg]
    indices: list[IndexCfg]


def _require(d: dict[str, Any], key: str, ctx: str) -> Any:
    if key not in d:
        raise ValueError(f"Missing required key '{key}' in {ctx}")
    return d[key]


def load_config(path: str) -> BenchCfg:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    project_name = _require(raw.get("project", {}), "name", "project")

    run_raw = _require(raw, "run", "root")
    run_cfg = RunCfg(
        output_root=_require(run_raw, "output_root", "run"),
        k_list=list(_require(run_raw, "k_list", "run")),
        topn=int(run_raw.get("topn", 10)),
        fail_fast=bool(run_raw.get("fail_fast", False)),
    )

    data_raw = _require(raw, "data", "root")
    data_cfg = DataCfg(
        queries_path=_require(data_raw, "queries_path", "data"),
        truth_key=str(data_raw.get("truth_key", "answer_ids")),
    )

    models_raw = _require(raw, "models", "root")
    models: dict[str, ModelCfg] = {}
    for model_name, m in models_raw.items():
        qe = _require(m, "query_embedding", f"models.{model_name}")
        emb = EmbeddingCfg(
            provider=str(_require(qe, "provider", f"models.{model_name}.query_embedding")),
            dim=int(_require(qe, "dim", f"models.{model_name}.query_embedding")),
            salt=str(qe.get("salt", "")),
            base_url=str(qe.get("base_rul", "")),
            endpoint_path=str(qe.get("endpoint_path", "/embed")),
            timeout_sec=int(qe.get("timeout_sec", 15)),
        )
        models[model_name] = ModelCfg(name=model_name, query_embedding=emb)

    indices_raw = _require(raw, "indices", "root")
    indices: list[IndexCfg] = []
    for idx in indices_raw:
        doc_vec_cfg = None
        if "docd_vector" in idx and idx["doc_vector"] is not None:
            dv = idx["doc_vector"]
            doc_vec_cfg = EmbeddingCfg(
                provider=str(_require(dv, "provider", f"indices.{idx.get('name','?')}.doc_vector")),
                dim=int(_require(dv, "dim", f"indicies.{idx.get('name','?')}.doc_vector")),
                salt=str(dv.get("salt", "")),
            )

        indices.append(
            IndexCfg(
                name=str(_require(idx, "name", "indices[*]")),
                backend=str(_require(idx, "backend", f"indices.{idx.get('name','?')}")),
                vector_field=str(_require(idx, "vector_field", f"indices.{idx.get('name','?')}")),
                docs_path=str(idx.get("docs_path", "")),
                id_field=str(idx.get("id_field", "doc_id")),
                label_field=str(idx.get("label_field", "answer_id")),
                doc_vector=doc_vec_cfg,
                es_url=str(idx.get("es_url", "")),
                es_index=str(idx.get("es_index", "")),
                es_auth_user=str(idx.get("es_auth_user", "")),
                es_auth_pass=str(idx.get("es_auth_pass", "")),
                es_verify_tls=bool(idx.get("es_verify_tls", True)),
                es_use_knn=bool(idx.get("es_use_knn", True)),
            )
        )

    return BenchCfg(
        project_name=project_name, run=run_cfg, data=data_cfg, models=models, indices=indices
    )
