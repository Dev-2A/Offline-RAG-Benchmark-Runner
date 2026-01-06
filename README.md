# Offline RAG Benchmark Runner (OBRBR)

Windows에서 **"복붙-실행"** 가능한 RAG/검색 벤치마크 러너(MVP)입니다.  
여러 인덱스에 대해 모델 A/B를 동일 조건으로 실행하고, **Recall@1/3/5/10** 결과를 **Excel + Markdown 리포트**로 남깁니다.

## Quickstart (Windows)

### Option 1) One-shot (추천)
```bat
run.cmd
```

### Option 2) Manual
```bat
call .venv\Scripts\activate.bat
python -m obrbr --config configs\bench.yaml
```

## Output
실행이 끝나면 아래 경로에 겨로가가 생성됩니다:  
- `results/YYYYMMDD_HHMM/`
  - `summary.xlsx`: Summary 시트 + Delta 시트 + (인덱스x모델) 상세 시트
  - `report.md`: KPI 요약 + A/B 델타 + 실패 목록(있다면)
  - `run.log`: 실행 로그(콘솔+파일)

## Config
- 기본 설정: `configs/bench.yaml`
- 주요 항목:
  - `indices`: 평가할 인덱스 목록
  - `run.k_list`: Recall@k 리스트 (예:`[1,3,5,10]`)
  - `data.queries_path`: 쿼리/정답 데이터(jsonl) 경로
  - `models`: 모델 A/B 쿼리 임베딩 방식

## Backends
- `mock` (기본): `data/mock_indices/**/docs.jsonl` 기반 in-memory cosine 검색
- `elasticsearch` (옵션): ES endpoint로 검색 (설정 필요)

## Models (MVP 기준)
- Model A: (기본) 로컬 해시 임베딩 → 검색 실행
- Model B: 외부 임베딩 API 또는 로컬 해시 임베딩 → 검색 실행
> MVP에서는 샘플 데이터 + mock backend로 로컬에서 바로 동작합니다.