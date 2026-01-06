# Offline RAG Benchmark Runner (OBRBR)

Windows에서 "복붙-실행" 가능한 RAG/검색 벤치마크 러너 MVP입니다.

## Quickstart (Windows)
```bat
run.cmd
```

## Output
- results/YYYYMMDD_HHMM/
  - summary.xlsx (요약 + 인덱스별 시트)
  - report.md (템플릿 기반 자동 리포트)
  - run.log (콘솔+파일 로깅)

## Config
- configs/bench.yaml

## Backends
- mock: data/mock_indices/**/docs.jsonl 기반 in-memory cosine 검색
- elasticsearch(옵션): ES endpoint로 knn/script_score 검색 (설정 필요)

## Models
- A: (기본) 로컬 해시 임베딩(내부) → 인덱스 벡터필드로 검색
- B: 외부 임베딩 API 또는 로컬 해시 임베딩 → 인덱스 벡터필드로 검색
> MVP에서는 샘플 데이터로 mock backend가 기본 동작합니다.