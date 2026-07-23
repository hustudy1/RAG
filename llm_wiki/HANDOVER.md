# 인수인계 문서 (HANDOVER)

---

## 1. 프로젝트 개요

- **프로젝트 이름**: rag
- **llm_wiki 가이드 버전**: v0.5.0
- **목적**: 임의의 폴더/파일을 가리켜 인덱싱하고 로컬 임베딩으로 검색 가능하게 만드는 범용 RAG(검색 증강 생성) 라이브러리. 향후 별도로 만들 LangGraph 기반 LLM 오케스트레이션 프로젝트가 검색(retrieval) 노드로 Python 함수 직접 import해서 쓸 하위 도구.
- **기술 스택**: Python 3.11 (uv로 관리), sentence-transformers(로컬 임베딩), chromadb(벡터 저장), pypdf(PDF 로딩). `anthropic`은 선택적 extra(`rag[answer]`)로만 필요.
- **주요 디렉터리**:
  - `src/rag/`: 라이브러리 소스 (loader/chunker/embeddings/store/cache/manifest/index/generation)
  - `tests/`: pytest 테스트
  - `scripts/quickstart.py`: 수동 end-to-end 검증 스크립트
  - `llm_wiki/`: AI 작업 지침 템플릿 (이 문서가 속한 폴더)

## 2. 실행 / 검증 방법

- **설치**: `uv sync --extra answer` (답변 생성 기능까지 쓰려면. 검색만 쓸 거면 `uv sync`로 충분)
- **개발 서버**: 해당 없음 (라이브러리이며 서버 아님)
- **빌드**: 해당 없음 (`uv sync`/`uv run` 시 hatchling이 자동 빌드)
- **테스트**: `uv run pytest -q`
- **린트/타입체크**: `[UNKNOWN]` — 아직 ruff/mypy 등 설정하지 않음
- **수동 확인 방법**: `uv run python scripts/quickstart.py --source <임의 폴더> --query "<질문>" [--k N] [--answer]`
- **마지막 검증**: 2026-07-22. `uv run pytest -q` → 10 passed. `scripts/quickstart.py --source llm_wiki --query "커밋과 푸시를 하기 전에 무엇을 해야 하나요?"`로 실제 llm_wiki 폴더(5개 파일, 32청크) 인덱싱 + 검색 확인. 재실행 시 `unchanged=5`로 증분 재인덱싱(재임베딩 없음) 확인.

## 3. 환경 / 주의사항

- **필요한 환경 변수**: `ANTHROPIC_API_KEY` — `RAGIndex.answer()`를 쓸 때만 필요. `build()`/`refresh()`/`search()`는 API 키 없이 항상 동작.
- **외부 서비스**: 핵심 경로에는 없음. 임베딩 모델(`all-MiniLM-L6-v2`)은 최초 1회 Hugging Face Hub에서 가중치를 받아와야 해서 그때만 인터넷 필요 — 이후엔 완전 오프라인(`~/.cache/huggingface`에 캐시됨).
- **로컬 전제조건**: Python 3.11 (시스템 기본 `python3`는 3.9.6이라 사용 불가). `/opt/homebrew/bin/python3.11`과 `uv`(`/opt/homebrew/bin/uv`) 사용.
- **건드리면 안 되는 리소스**: 없음
- **승인이 필요한 작업**: `git commit`/`push` (매번 실행 직전 사용자 승인 필요 — llm_wiki 규칙). 현재 이 프로젝트는 git 저장소가 아니며, 초기화 여부는 아래 "미해결 문제" 참고.

## 4. 현재 상태 (최종 갱신: 2026-07-22)

RAG 라이브러리 핵심 기능(폴더 인덱싱, 증분 재인덱싱, 검색, 선택적 답변 생성)을 구현 완료했다.
단위·통합 테스트 10개 모두 통과했고, `scripts/quickstart.py`로 실제 `llm_wiki/` 폴더를 대상으로
수동 end-to-end 검증까지 마쳤다. 아직 git 저장소로 초기화하지 않았고, 이 RAG를 소비할
LangGraph 기반 오케스트레이션 프로젝트는 별도 작업으로 아직 시작하지 않았다.

## 5. 작업 로그 (최신이 위)

### 2026-07-22 — RAG 라이브러리 초기 구현
- **한 일**:
  - `pyproject.toml`, `.python-version`(3.11), `.gitignore` 작성. `uv venv --python 3.11` + `uv sync --extra answer`로 의존성 설치(핵심: sentence-transformers, chromadb, pypdf, numpy / 선택: anthropic / dev: pytest).
  - `src/rag/`에 `constants.py`, `types.py`, `loader.py`, `chunker.py`, `embeddings.py`, `store.py`, `cache.py`, `manifest.py`, `index.py`(`RAGIndex`), `generation.py`, `__init__.py` 구현.
  - `tests/`에 `conftest.py`, `test_loader.py`, `test_index_build_and_search.py`, `test_incremental_refresh.py` 작성. `uv run pytest -q` 10개 전부 통과.
  - `scripts/quickstart.py` 작성 및 `llm_wiki/` 폴더로 수동 검증(최초 인덱싱 5개 파일/32청크, 재실행 시 `unchanged=5`로 증분 확인).
  - `CLAUDE.md`, `AGENTS.md`, `llm_wiki/HANDOVER.md`(이 문서) 작성.
  - `.claude/settings.local.json`에 이번 세션에 필요한 Bash 명령·Write/Edit 허용 목록 추가(`defaultMode: acceptEdits`) — 사용자가 반복적으로 권한 프롬프트 없이 진행해달라고 요청해서 반영.
- **이유/결정**:
  - 대화를 통해 "모든 곳에서 쓸 수 있는 RAG"를 (1) Python 함수 직접 import 연동, (2) 임의 폴더 인덱싱 범용 도구, (3) 로컬 임베딩(비용·API키·인터넷 의존 없음)으로 구체화했다. LangGraph 기반 오케스트레이션은 별도 프로젝트로 분리하기로 했고(이번 작업 범위 아님), RAG는 그 오케스트레이션이 검색 노드로 호출할 하위 도구로 설계했다.
  - 벡터 스토어는 Chroma를 선택했다 — FAISS는 메타데이터/영속성/upsert-by-id를 직접 구현해야 해서 이 규모에 과한 자체 인프라가 필요하고, LanceDB는 검증이 덜 됐고 무거운 의존성을 끌고 온다.
  - 캐시 위치는 소스 폴더 내부(`.rag_index/`)가 아니라 중앙 캐시(`~/.cache/rag_lib/<경로 해시>`)로 결정했다 — 소스 폴더가 읽기 전용이거나 남의 코드베이스일 수 있어서다.
  - 청킹은 langchain 등 의존성 추가 없이 자체 재귀 분할기로 구현했다(80줄 내외라 별도 의존성이 불필요하다고 판단).
  - `RAGIndex.answer()`는 `anthropic`을 메서드 내부에서만 지연 import해서, 핵심 검색 경로(`search`/`build`/`refresh`)가 API 키 없이 항상 동작하도록 분리했다.
- **결과**: `uv run pytest -q` 10 passed. `scripts/quickstart.py` 수동 실행으로 실제 `llm_wiki/` 폴더 인덱싱 + 한국어 질의 검색 + 재실행 시 증분 인덱싱(`unchanged=5`) 확인. 답변 생성(`.answer()`, `--answer` 플래그)은 `ANTHROPIC_API_KEY` 없이는 테스트하지 않아 코드 경로만 작성했고 실제 호출은 미검증이다.
- **Git 상태**: 이 저장소는 아직 git 저장소가 아니다(초기화 여부 미정, 사용자 확인 필요). 커밋 없음.
- **실패한 시도**:
  - 최초 `uv sync --extra answer`를 `src/rag/` 소스 파일 작성 전에 실행해서 빈 패키지가 설치됐다 → `uv sync --reinstall-package rag --extra answer`로 재빌드해서 해결. 앞으로 소스 변경이 재설치에 반영 안 되면 이 명령을 다시 쓴다.
  - 증분 인덱싱 테스트 2개가 처음엔 실패했다 — 라이브러리 버그가 아니라 테스트 픽스처가 `persist_dir`을 `source_dir` 내부(둘 다 같은 `tmp_path`)에 둬서, Chroma가 쓰는 `manifest.json`이 `.json` 확장자 때문에 재인덱싱 대상으로 잡힌 것이었다. `loader.iter_documents`에 `exclude_dirs` 파라미터를 추가해 `RAGIndex`가 자신의 `persist_dir`을 항상 워크 대상에서 제외하도록 방어 코드를 넣어 해결했다(실사용에서 `persist_dir`을 `source_dir` 안에 두는 경우에도 안전).

## 6. 미해결 문제 / 모르는 부분

| 항목 | 상태 | 설명 |
|------|------|------|
| git 저장소 초기화 여부 | `[UNKNOWN]` | 이 프로젝트를 git으로 추적할지, `llm_wiki/.git`(clone 원본)을 어떻게 처리할지 사용자 확인 필요 |
| `.answer()` 실제 Claude 호출 검증 | `[UNVERIFIED]` | 코드는 작성했지만 실제 `ANTHROPIC_API_KEY`로 호출까지는 테스트하지 않음 |
| 로컬 임베딩(`all-MiniLM-L6-v2`)의 한국어 검색 품질 | `[UNVERIFIED]` | quickstart.py로 한국어 질의 검색은 동작했지만, 이 모델은 영어 위주로 학습되어 한국어 문서가 많은 경우 품질이 기대보다 낮을 수 있음. 다국어 모델(예: `paraphrase-multilingual-MiniLM-L12-v2`)로 교체가 필요할 수 있음 |
| 린트/타입체크 설정 | `[UNKNOWN]` | ruff/mypy 등 아직 설정하지 않음 |

## 7. 다음에 할 일 (우선순위 순)

1. git 저장소 초기화 여부 확인 후 필요 시 `git init` + 첫 커밋 (사용자 승인 필요)
2. 한국어 문서 검색 품질 확인 — 필요하면 `embedding_model`을 다국어 모델로 교체 검토
3. 이 RAG 프로젝트를 검색 노드로 import할 LangGraph 기반 오케스트레이션 프로젝트를 별도로 시작
4. (선택) `RAGIndex.answer()`를 실제 `ANTHROPIC_API_KEY`로 end-to-end 검증

## 8. 주요 의사결정 기록

| 날짜 | 결정 | 이유 | 출처/근거 |
|------|------|------|-----------|
| 2026-07-22 | 벡터 스토어로 Chroma 채택 | 서버 없이 영속, upsert/delete-by-id가 요구사항에 정확히 맞음 | 대화 중 설계 논의 + Plan 서브에이전트 검토 |
| 2026-07-22 | 임베딩은 로컬(sentence-transformers) 채택, Voyage/OpenAI 미사용 | 비용·API키·인터넷 의존 없이 "모든 곳에서" 동작해야 한다는 요구사항 | 사용자 명시적 결정 |
| 2026-07-22 | RAG와 오케스트레이션(LangGraph)을 별도 프로젝트로 분리 | RAG는 재사용 가능한 검색 하위 도구, 오케스트레이션은 이를 소비하는 상위 계층 | 사용자 명시적 결정 |
| 2026-07-22 | 캐시 위치를 중앙(`~/.cache/rag_lib`)으로 결정, in-folder 캐시 미사용 | 소스 폴더가 읽기 전용이거나 남의 코드베이스일 수 있음 | 설계 논의(Plan 서브에이전트) |

## 9. 참고 자료

- 이 프로젝트의 구현 계획 문서: `~/.claude/plans/jiggly-gathering-kay.md` (확인일: 2026-07-22)
