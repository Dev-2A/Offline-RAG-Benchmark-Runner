from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

from .config import BenchCfg, IndexCfg, load_config
from .embedder import Embedder
from .logging_utils import setup_logger
from .metrics import QueryEval, recall_table
from .reporting import render_summary_table_md, write_summary_xlsx
from .search import ElasticsearchBackend, MockBackend
from .search.backend_base import SearchHit


def _now_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def _read_queries(path: str) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def _make_backend(idx: IndexCfg):
    b = idx.backend.lower()
    if b == "mock":
        return MockBackend(idx)
    if b == "elasticsearch":
        return ElasticsearchBackend(idx)
    raise ValueError(f"[{idx.name}] Unknown backend: {idx.backend}")


def _truth_set(q: Dict[str, object], truth_key: str) -> set[str]:
    v = q.get(truth_key, [])
    if isinstance(v, list):
        return {str(x) for x in v}
    return {str(v)}


def _ranked_labels(hits: List[SearchHit]) -> List[str]:
    return [h.label for h in hits]


def _as_float(x: object, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _top_deltas(delta_rows: List[Dict[str, object]], key: str, n: int = 3) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    valid = [r for r in delta_rows if key in r and str(r.get(key, "")).strip() != ""]
    valid.sort(key=lambda r: _as_float(r.get(key, 0.0)), reverse=True)
    best = valid[:n]
    worst = list(reversed(valid[-n:])) if len(valid) >= n else list(reversed(valid))
    return best, worst


def run_benchmark(config_path: str) -> None:
    cfg: BenchCfg = load_config(config_path)

    run_id = _now_run_id()
    out_dir = os.path.join(cfg.run.output_root, run_id)
    os.makedirs(out_dir, exist_ok=True)

    logger = setup_logger(os.path.join(out_dir, "run.log"))
    logger.info(f"Project: {cfg.project_name}")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Config: {config_path}")
    logger.info(f"Output dir: {out_dir}")

    queries = _read_queries(cfg.data.queries_path)
    logger.info(f"Loaded queries: {len(queries)} from {cfg.data.queries_path}")

    summary_rows: List[Dict[str, object]] = []
    per_index_sheets: Dict[str, List[Dict[str, object]]] = {}
    failures: List[str] = []

    # ---- main loop: indices x models ----
    for idx in cfg.indices:
        logger.info(f"=== Index: {idx.name} (backend={idx.backend}) ===")

        try:
            backend = _make_backend(idx)
        except Exception as e:
            msg = f"[INDEX INIT FAIL] {idx.name}: {e}"
            logger.exception(msg)
            failures.append(msg)
            if cfg.run.fail_fast:
                raise
            continue

        for model_name, model_cfg in cfg.models.items():
            logger.info(f"-- Model {model_name} --")
            evals: List[QueryEval] = []
            details_rows: List[Dict[str, object]] = []

            try:
                embedder = Embedder(model_cfg.query_embedding)

                for q in queries:
                    qid = str(q.get("query_id", ""))
                    question = str(q.get("question", ""))
                    truth = _truth_set(q, cfg.data.truth_key)

                    qvec = embedder.embed(question)
                    hits = backend.search(qvec, topn=cfg.run.topn)
                    ranked = _ranked_labels(hits)

                    evals.append(QueryEval(query_id=qid, truth=truth, ranked_labels=ranked))

                    row: Dict[str, object] = {
                        "query_id": qid,
                        "question": question,
                        "truth": ",".join(sorted(truth)),
                    }

                    for i in range(min(cfg.run.topn, len(hits))):
                        row[f"rank_{i+1}_label"] = hits[i].label
                        row[f"rank_{i+1}_score"] = round(hits[i].score, 6)

                    for k in cfg.run.k_list:
                        row[f"hit@{k}"] = any(x in truth for x in ranked[:k])

                    details_rows.append(row)

                rec = recall_table(evals, cfg.run.k_list)
                summary: Dict[str, object] = {
                    "index": idx.name,
                    "model": model_name,
                    "queries": len(evals),
                }
                for k in cfg.run.k_list:
                    summary[f"recall@{k}"] = round(rec[k], 4)

                summary_rows.append(summary)

                sheet_key = f"{idx.name}_{model_name}"
                per_index_sheets[sheet_key] = details_rows

                logger.info(
                    "Result: "
                    + ", ".join([f"R@{k}={summary[f'recall@{k}']}" for k in cfg.run.k_list])
                )

            except Exception as e:
                msg = f"[RUN FAIL] index={idx.name}, model={model_name}: {e}"
                logger.exception(msg)
                failures.append(msg)
                if cfg.run.fail_fast:
                    raise
                summary_rows.append({"index": idx.name, "model": model_name, "queries": 0, "error": str(e)})
                continue

    # ---- Build A vs B delta summary per index (if both exist) ----
    delta_rows: List[Dict[str, object]] = []
    by_index: Dict[str, Dict[str, Dict[str, object]]] = {}
    for r in summary_rows:
        idx_name = str(r.get("index", ""))
        model = str(r.get("model", ""))
        by_index.setdefault(idx_name, {})[model] = r

    for idx_name, m in by_index.items():
        if "A" in m and "B" in m and ("error" not in m["A"]) and ("error" not in m["B"]):
            row: Dict[str, object] = {"index": idx_name}

            for k in cfg.run.k_list:
                a = _as_float(m["A"].get(f"recall@{k}", 0.0))
                b = _as_float(m["B"].get(f"recall@{k}", 0.0))
                row[f"delta@{k} (A-B)"] = round(a - b, 4)

            # winner by R@1 then R@3
            a1 = _as_float(m["A"].get("recall@1", 0.0))
            b1 = _as_float(m["B"].get("recall@1", 0.0))
            if a1 > b1:
                row["winner"] = "A"
            elif b1 > a1:
                row["winner"] = "B"
            else:
                a3 = _as_float(m["A"].get("recall@3", 0.0))
                b3 = _as_float(m["B"].get("recall@3", 0.0))
                row["winner"] = "A" if a3 >= b3 else "B"

            delta_rows.append(row)

    # ---- Winner summary & highlights ----
    winner_counts = {"A": 0, "B": 0}
    for r in delta_rows:
        w = str(r.get("winner", "")).strip()
        if w in winner_counts:
            winner_counts[w] += 1

    winner_summary_md = (
        f"- Indices compared (A vs B pairs): {len(delta_rows)}\n"
        f"- Winner count: A={winner_counts['A']}, B={winner_counts['B']}\n"
    )

    best, worst = _top_deltas(delta_rows, key="delta@1 (A-B)", n=3)

    def _bullets(rows: List[Dict[str, object]], title: str) -> str:
        if not rows:
            return f"- {title}: _None_\n"
        s = f"- {title}:\n"
        for r in rows:
            s += f"  - {r.get('index')} : delta@1 (A-B)={r.get('delta@1 (A-B)')} (winner={r.get('winner')})\n"
        return s

    delta_highlights_md = ""
    delta_highlights_md += _bullets(best, "Top improvements (A-B) by R@1")
    delta_highlights_md += _bullets(worst, "Top regressions (A-B) by R@1")

    # ---- Write xlsx (Summary + Delta + detail sheets) ----
    xlsx_path = os.path.join(out_dir, "summary.xlsx")
    write_summary_xlsx(
        xlsx_path,
        summary_rows=summary_rows,
        per_index_sheets=per_index_sheets,
        extra_sheets={"Delta": delta_rows},
    )
    logger.info(f"Wrote: {xlsx_path}")

    # ---- Write report.md using template ----
    template_path = os.path.join("templates", "report_template.md")
    with open(template_path, "r", encoding="utf-8") as f:
        tpl = f.read()

    summary_md = render_summary_table_md(summary_rows)
    delta_md = render_summary_table_md(delta_rows) if delta_rows else "_No A/B pairs_"

    failures_md = "_None_"
    if failures:
        failures_md = "\n".join([f"- {x}" for x in failures])

    report = tpl.format(
        project_name=cfg.project_name,
        run_id=run_id,
        started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        config_path=config_path,
        summary_table_md=summary_md,
        delta_table_md=delta_md,
        winner_summary_md=winner_summary_md,
        delta_highlights_md=delta_highlights_md,
        failures_md=failures_md,
    )

    report_path = os.path.join(out_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Wrote: {report_path}")

    logger.info("All done. (이제 벤치마크가 도망갈 곳이 없습니다.)")
