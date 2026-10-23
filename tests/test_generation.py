"""generate_answer()가 실제 anthropic SDK로 요청을 만들고 응답을 읽는지 확인한다.

네트워크나 API 키 없이 돈다. SDK는 진짜를 쓰고, HTTP 전송만 가짜 응답으로 바꾼다.
그래서 SDK 메이저 버전이 바뀌어 요청·응답 형식이 달라지면 이 테스트가 깨진다.
"""

import json

import pytest

anthropic = pytest.importorskip("anthropic")
# anthropic 2.x는 httpx2를, 그 전 버전은 httpx를 HTTP 클라이언트로 쓴다 (2026-10-22 확인)
try:
    import httpx2 as httpx
except ImportError:  # pragma: no cover - anthropic < 2
    httpx = pytest.importorskip("httpx")

from rag.generation import generate_answer  # noqa: E402
from rag.types import Chunk  # noqa: E402


def _chunk(text, path="docs/a.md"):
    return Chunk(text=text, source_path="/x/" + path, relative_path=path, chunk_index=0, score=0.9)


def test_generate_answer_round_trip(monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": seen["body"]["model"],
                "content": [{"type": "text", "text": "답: 42 [docs/a.md]"}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        )

    real_client = anthropic.Anthropic

    def fake_client(*args, **kwargs):
        return real_client(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    monkeypatch.setattr(anthropic, "Anthropic", fake_client)

    answer = generate_answer("질문?", [_chunk("정답은 42다.")], model="claude-opus-5-5", max_tokens=100)

    assert answer == "답: 42 [docs/a.md]"
    assert seen["url"].endswith("/v1/messages")
    assert seen["body"]["model"] == "claude-opus-5-5"
    assert seen["body"]["max_tokens"] == 100
    prompt = seen["body"]["messages"][0]["content"]
    assert "[docs/a.md]" in prompt and "정답은 42다." in prompt and "질문?" in prompt
