# ==========================================================================
# 3.8 아카이브 - AI Q&A 챗봇 백엔드 (Vercel Serverless Function)
# POST /api/ask  { "question": "..." }  ->  { "answer": "..." }  또는  { "error": "..." }
#
# Vercel의 Python 런타임은 이 파일에서 BaseHTTPRequestHandler를 상속한
# `handler` 클래스를 자동으로 서버리스 함수로 인식합니다.
# ==========================================================================

from http.server import BaseHTTPRequestHandler
import json
import os

import anthropic

# 기획안에 명시된 시스템 프롬프트 (챗봇의 역할과 답변 원칙을 고정)
SYSTEM_PROMPT = (
    "너는 3.8민주의거 역사 안내 챗봇이다. 1960년 3월 8일부터 10일까지 "
    "대전 고등학생들이 이승만 정권에 항거한 학생운동인 3.8민주의거에 대해 "
    "친절하고 정확하게 답변해라. 확실하지 않은 정보는 추측하지 말고 "
    "기념관에 문의하도록 안내해라."
)

MODEL = "claude-opus-5"
GENERIC_ERROR = "오류가 발생했습니다. 잠시 후 다시 시도해주세요."


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # --- 1. 요청 본문 파싱 ---------------------------------------------
        try:
            content_length = int(self.headers.get("Content-Length", 0) or 0)
            raw_body = self.rfile.read(content_length) if content_length else b""
            body = json.loads(raw_body.decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "요청 형식이 올바르지 않습니다."})
            return

        question = (body.get("question") or "").strip()

        # 실패 처리 1: 빈 질문 입력 (프론트에서도 막지만 서버에서도 한 번 더 확인)
        if not question:
            self._send_json(400, {"error": "질문을 입력해주세요."})
            return

        # API 키는 반드시 환경변수로만 읽는다 (코드에 하드코딩 금지)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            self._send_json(500, {"error": "서버에 API 키가 설정되어 있지 않습니다."})
            return

        # --- 2. Anthropic API 호출 -----------------------------------------
        try:
            client = anthropic.Anthropic(api_key=api_key, timeout=25.0)
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                # 단답형 Q&A이므로 낮은 effort로 응답 속도를 우선함
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": question}],
            )

            answer = next(
                (block.text for block in response.content if block.type == "text"),
                "",
            )

            if not answer:
                raise ValueError("empty answer")

            self._send_json(200, {"answer": answer})

        # 실패 처리 2: Anthropic API가 4xx/5xx 오류를 반환한 경우
        except anthropic.APIStatusError:
            self._send_json(502, {"error": GENERIC_ERROR})
        except anthropic.APIConnectionError:
            self._send_json(502, {"error": GENERIC_ERROR})
        except Exception:
            self._send_json(500, {"error": GENERIC_ERROR})

    def do_OPTIONS(self):
        # 브라우저의 CORS preflight 요청에 대한 응답
        self.send_response(204)
        self._write_cors_headers()
        self.end_headers()

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._write_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
