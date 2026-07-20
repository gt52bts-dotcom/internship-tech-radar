from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


VALID_SCENARIOS = {
    "normal",
    "quote_500",
    "confirmation_timeout",
    "frontend_js_error",
}


class MockInsuranceHandler(BaseHTTPRequestHandler):
    scenario = "normal"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/health":
            self._send_json(200, {"status": "ok", "scenario": self.scenario})
            return

        if path == "/api/client-errors":
            errors = []
            if self.scenario == "frontend_js_error":
                errors.append(
                    {
                        "type": "TypeError",
                        "message": "Cannot read properties of undefined while rendering quote summary",
                        "step": "render_quote_summary",
                    }
                )
            self._send_json(200, {"errors": errors, "scenario": self.scenario})
            return

        if path == "/":
            self._send_html(200, self._html())
            return

        self._send_json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self._read_json_body()

        if path == "/api/quote":
            if self.scenario == "quote_500":
                self._send_json(
                    500,
                    {
                        "error": "quote_service_failed",
                        "message": "mock quote engine returned 500",
                        "safe_to_retry": True,
                    },
                )
                return

            coverage = int(payload.get("coverage", 1_000_000))
            premium = max(500, round(coverage * 0.0012))
            self._send_json(
                200,
                {
                    "quote_id": "QT-MOCK-001",
                    "premium": premium,
                    "currency": "TWD",
                    "valid_minutes": 15,
                },
            )
            return

        if path == "/api/application/preview":
            if self.scenario == "confirmation_timeout":
                time.sleep(3)

            self._send_json(
                200,
                {
                    "application_preview_id": "APP-PREVIEW-001",
                    "status": "preview_only",
                    "policy_issued": False,
                    "payment_charged": False,
                    "pii_used": False,
                },
            )
            return

        self._send_json(404, {"error": "not_found", "path": path})

    def _html(self) -> str:
        return """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>Mock 線上投保</title>
  <style>
    body { font-family: Arial, "Microsoft JhengHei", sans-serif; margin: 40px; line-height: 1.55; }
    main { max-width: 760px; }
    .badge { display: inline-block; padding: 4px 8px; border: 1px solid #456; border-radius: 4px; }
    code { background: #f1f3f5; padding: 2px 4px; }
  </style>
</head>
<body>
  <main>
    <span class="badge">Mock only</span>
    <h1>線上投保測試流程</h1>
    <p>這個頁面只用於穩定性黑箱 PoC，不會付款、不會出單、不使用客戶個資。</p>
    <ol>
      <li>載入投保首頁</li>
      <li>呼叫報價 API</li>
      <li>建立付款前確認預覽</li>
      <li>檢查前端錯誤紀錄</li>
    </ol>
    <p>目前情境：<code>""" + self.scenario + """</code></p>
  </main>
</body>
</html>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mock online insurance app for black-box reliability PoC.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    parser.add_argument("--scenario", default="normal", choices=sorted(VALID_SCENARIOS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    MockInsuranceHandler.scenario = args.scenario
    server = ThreadingHTTPServer((args.host, args.port), MockInsuranceHandler)
    print(f"Mock insurance app listening on http://{args.host}:{args.port} scenario={args.scenario}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock insurance app.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
