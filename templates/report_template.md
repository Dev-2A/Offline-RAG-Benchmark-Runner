# Offline RAG Benchmark Report

- Project: {project_name}
- Run ID: {run_id}
- Started at: {started_at}
- Config: {config_path}

## Executive Summary
- 목적: 모델 A/B 검색 성능(Recall@k) 비교
- 범위: 인덱스별 평가 + 실패 격리(일부 인덱스 실패해도 전체 런은 계속)

## Winner Summary
{winner_summary_md}

## Delta Highlights
{delta_highlights_md}

## KPI Summary (Per Index × Model)
{summary_table_md}

## A vs B Delta (A-B)
{delta_table_md}

## Failures
{failures_md}

## Notes
- Recall@k는 정답(answer_id)이 Top-k 결과에 포함되었는지 기준으로 계산합니다.
- summary.xlsx에는 Summary 시트 + Delta 시트 + 인덱스×모델 상세 시트가 생성됩니다.
