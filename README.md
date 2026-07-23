# rag

임의의 폴더나 파일을 가리키면, 로컬에서 검색 가능한 인덱스로 만들어주는 범용 RAG(검색 증강 생성) 라이브러리다.
API 키나 서버 없이 Python 함수 import만으로 쓸 수 있게 만들었다.

## 특징

- **어디서든 동작**: 임베딩을 로컬 모델(sentence-transformers)로 계산한다. 최초 1회 모델 가중치를
  다운로드하는 것 외에는 인터넷도, API 키도 필요 없다.
- **아무 폴더나 인덱싱 가능**: 특정 프로젝트에 고정된 도구가 아니다. `RAGIndex(source_dir=...)`에
  원하는 폴더 경로만 넘기면 된다.
- **증분 인덱싱**: 한 번 인덱싱한 뒤 다시 `refresh()`를 호출하면, 바뀐 파일만 다시 처리한다.
  전체 재인덱싱이 필요 없다.
- **순수 Python 함수 호출**: MCP 서버도, HTTP API도 아니다. `import rag`만 하면 된다. 다른 프로젝트
  (예: LangGraph 기반 오케스트레이션 프로젝트)에서 검색 도구로 바로 가져다 쓸 수 있게 설계했다.
- **소스 폴더를 건드리지 않음**: 인덱스 캐시는 소스 폴더 안이 아니라 `~/.cache/rag_lib/`
  아래 중앙 위치에 저장된다. 읽기 전용 폴더나 남의 코드베이스를 가리켜도 안전하다.

## 설치

```bash
uv sync              # 검색 기능만 필요할 때
uv sync --extra answer   # 검색 결과를 Claude로 답변까지 생성하는 기능도 쓸 때
```

Python 3.11 이상이 필요하다. (macOS 시스템 기본 `python3`는 3.9라서 안 됨 — `uv`가 알아서
올바른 버전을 받아 가상환경을 만든다.)

## 사용법

```python
from rag import RAGIndex

# 1. 인덱스 만들기 — 아무 폴더나 지정
index = RAGIndex(source_dir="/path/to/any/folder")

# 2. 최초 인덱싱
index.build()

# 3. 이후 실행에서는 변경된 파일만 반영
index.refresh()

# 4. 검색
chunks = index.search("찾고 싶은 내용", k=5)
for c in chunks:
    print(c.relative_path, c.score, c.text[:100])

# 5. (선택) 검색 결과를 근거로 Claude가 답변까지 생성
#    rag[answer] 설치 + ANTHROPIC_API_KEY 환경변수 필요
answer = index.answer("찾고 싶은 내용")
print(answer.text)
```

### 명령줄로 바로 테스트해보기

```bash
uv run python scripts/quickstart.py --source <폴더 경로> --query "질문" [--k 5] [--answer]
```

## 지원하는 파일 형식

| 종류 | 확장자 |
|---|---|
| 문서/텍스트 | `.md` `.markdown` `.txt` `.rst` |
| 코드 | `.py` `.js` `.jsx` `.ts` `.tsx` `.java` `.go` `.rb` `.rs` `.c` `.h` `.cpp` `.hpp` `.cs` `.sh` `.sql` `.html` `.css` |
| 설정/데이터 | `.yaml` `.yml` `.json` `.toml` `.ini` `.cfg` |
| 문서 파일 | `.pdf` (텍스트 추출, `pypdf` 사용) |

지원 목록에 없는 확장자, 10MB 초과 파일, 바이너리 파일(텍스트 확장자인데 실제로는 바이너리인 경우),
손상된 PDF는 전체 인덱싱을 중단시키지 않고 자동으로 건너뛴다.

다음 폴더는 항상 무시한다: `.git` `node_modules` `__pycache__` `.venv` `dist` `build` 등
(이름이 `.`으로 시작하는 숨김 폴더도 기본적으로 모두 무시).

## 잘 동작하는 조건 / 한계

- **영어 문서에서 검색 품질이 가장 좋다.** 기본 임베딩 모델(`all-MiniLM-L6-v2`)이 영어 위주로
  학습된 모델이라, 한국어 문서가 대부분인 폴더에서는 검색 정확도가 기대보다 낮을 수 있다.
  한국어 비중이 크다면 `RAGIndex(embedding_model="paraphrase-multilingual-MiniLM-L12-v2")`처럼
  다국어 모델로 바꾸는 걸 고려할 것.
- **문서/코드 혼합 폴더에 무난하게 동작.** 청킹 전략이 문단(`\n\n`) → 줄(`\n`) → 문장 → 단어
  순으로 나누기 때문에, 산문 문서와 소스 코드 둘 다 적당히 잘 쪼개진다. 다만 코드 전용으로
  함수/클래스 경계를 인식하는 정교한 파싱은 하지 않는다(v1 범위 밖).
- **`persist_dir`를 명시적으로 지정할 때** `source_dir` 내부에 두지 않는 걸 권장한다
  (기본값처럼 중앙 캐시를 쓰면 이 문제 자체가 없음). 굳이 내부에 둬도 자기 자신의 캐시 폴더는
  인덱싱 대상에서 자동 제외하도록 되어 있어 안전하다.
- **`.answer()`는 아직 실제 API 호출로 검증하지 않았다.** 코드 경로는 작성했지만
  `ANTHROPIC_API_KEY`로 실제 호출 테스트는 안 해봄.

## 동작 원리 (간단히)

```
build() / refresh()
  1. source_dir을 순회하며 지원하는 파일들을 읽는다 (loader.py)
  2. 각 파일을 800자 단위, 150자 겹침으로 잘게 나눈다 (chunker.py)
  3. 각 조각을 로컬 임베딩 모델로 벡터화한다 (embeddings.py)
  4. 벡터를 Chroma(로컬 벡터DB)에 저장한다 (store.py)
  5. 파일별 mtime/size/내용 해시를 매니페스트에 기록해서,
     다음 실행 때 바뀐 파일만 다시 처리할 수 있게 한다 (manifest.py)

search()
  1. 질문을 같은 임베딩 모델로 벡터화
  2. Chroma에서 가장 비슷한 벡터를 가진 조각들을 찾아 반환

answer() [선택]
  검색된 조각들을 컨텍스트로 Claude에 전달해 근거를 인용한 답변을 생성
```

## 테스트

```bash
uv run pytest -q
```

`tests/`에는 파일 로딩(무시 패턴, 바이너리 스킵), 인덱싱+검색, 증분 재인덱싱(추가/수정/삭제 감지)에
대한 테스트가 있다.

## 프로젝트 구조

```
src/rag/
├── __init__.py      # 공개 API: RAGIndex, Chunk, BuildStats, Answer
├── types.py         # 데이터클래스 (Chunk, BuildStats, Answer)
├── constants.py      # 기본 설정값 (무시 폴더, 지원 확장자, 청크 크기 등)
├── loader.py         # 폴더 순회 + 파일 로딩
├── chunker.py         # 텍스트 분할
├── embeddings.py       # 로컬 임베딩 모델 래퍼
├── store.py           # Chroma 벡터 스토어 래퍼
├── cache.py           # 캐시 경로 결정
├── manifest.py         # 증분 인덱싱용 파일별 변경 추적
├── index.py           # RAGIndex — 위 컴포넌트들을 조립
└── generation.py       # 선택적 답변 생성 (anthropic 지연 import)
tests/                 # pytest 테스트
scripts/quickstart.py    # 수동 실행 데모
llm_wiki/               # AI 코딩 작업 지침 (llm_wiki/HANDOVER.md에 상세 작업 이력 있음)
```

이 프로젝트의 설계 배경, 미해결 항목, 다음 할 일은 `llm_wiki/HANDOVER.md`에 더 자세히 기록되어 있다.
