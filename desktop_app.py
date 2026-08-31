"""
3.8 아카이브 - 배포용 실행파일(.exe) 런처

정적 페이지(index.html 등)와 AI 챗봇 API(/api/ask)를 하나의 로컬 서버로 띄우고
기본 브라우저를 자동으로 연다. PyInstaller로 --onefile 빌드해서 배포한다.

API 키 설정 방법 (둘 중 하나):
  1) 환경변수 ANTHROPIC_API_KEY 지정
  2) 이 실행파일과 같은 폴더에 api_key.txt 파일을 만들고 키 값만 한 줄로 저장
키가 없어도 나머지 페이지는 정상 동작하며, 챗봇 질문 시에만 오류 메시지가 표시된다.
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

SYSTEM_PROMPT = (
    "너는 3.8민주의거 역사 안내 챗봇이다. 1960년 3월 8일부터 10일까지 "
    "대전 고등학생들이 이승만 정권에 항거한 학생운동인 3.8민주의거에 대해 "
    "친절하고 정확하게 답변해라. 확실하지 않은 정보는 추측하지 말고 "
    "기념관에 문의하도록 안내해라."
)
MODEL = "claude-opus-5"
GENERIC_ERROR = "오류가 발생했습니다. 잠시 후 다시 시도해주세요."


def app_dir():
    """실행파일(또는 스크립트)이 위치한 폴더 - api_key.txt를 찾는 기준 경로."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def static_dir():
    """정적 파일이 위치한 폴더 - PyInstaller onefile이면 임시 번들 폴더(_MEIPASS)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def load_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key.strip()

    key_file = os.path.join(app_dir(), "api_key.txt")
    if os.path.isfile(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    return None


STATIC_DIR = static_dir()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, fmt, *args):
        print("[서버]", fmt % args)

    def do_POST(self):
        if self.path != "/api/ask":
            self._send_json(404, {"error": "not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0) or 0)
            raw_body = self.rfile.read(content_length) if content_length else b""
            body = json.loads(raw_body.decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "요청 형식이 올바르지 않습니다."})
            return

        question = (body.get("question") or "").strip()
        if not question:
            self._send_json(400, {"error": "질문을 입력해주세요."})
            return

        api_key = load_api_key()
        if not api_key:
            self._send_json(
                500,
                {"error": "API 키가 설정되어 있지 않습니다. api_key.txt를 확인해주세요."},
            )
            return

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key, timeout=25.0)
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
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

        except anthropic.APIStatusError:
            self._send_json(502, {"error": GENERIC_ERROR})
        except anthropic.APIConnectionError:
            self._send_json(502, {"error": GENERIC_ERROR})
        except Exception:
            self._send_json(500, {"error": GENERIC_ERROR})

    def do_OPTIONS(self):
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


def main():
    port = 8000
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]

    url = f"http://127.0.0.1:{port}/index.html"
    print("=" * 60)
    print("3.8 아카이브 로컬 서버를 시작합니다.")
    print(f"주소: {url}")
    if not load_api_key():
        print("[안내] ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("       챗봇 기능을 쓰려면 이 파일과 같은 폴더에 api_key.txt를 만들고")
        print("       Anthropic API 키를 한 줄로 저장하세요.")
    print("종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.")
    print("=" * 60)

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
