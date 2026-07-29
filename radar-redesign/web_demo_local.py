"""Run the S1-S5 web demo locally without creating any AWS resources.

This is a development/demo adapter only.  It retains artifacts in memory and
exposes the same routes as the AWS Lambda API beneath ``/api``.
"""

from __future__ import annotations

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any

from agentic_cloud_radar.s1 import build_direct_url_scan, build_scan
from agentic_cloud_radar.s2 import build_compare
from agentic_cloud_radar.s3 import build_evaluate
from agentic_cloud_radar.s4 import build_validate
from agentic_cloud_radar.s5 import build_report


ARTIFACTS: dict[str, dict[str, dict[str, Any]]] = {}
WEB_ROOT = Path(__file__).resolve().parent / "web"


class RadarDemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/config.js":
            return self._json_text("window.RADAR_CONFIG = { apiBaseUrl: '/api' };\n", "application/javascript")
        if self.path == "/api/health":
            return self._json({"status": "ok"})
        if self.path.startswith("/api/runs/") and "/artifacts/" in self.path:
            _, _, tail = self.path.partition("/api/runs/")
            run_id, _, stage = tail.partition("/artifacts/")
            return self._json(ARTIFACTS[run_id][stage])
        return super().do_GET()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        try:
            payload = self._request_json()
            path = self.path.removeprefix("/api")
            if path == "/runs/url":
                scan = build_direct_url_scan(str(payload.get("url") or "")).to_dict()
                compare = build_compare(scan).to_dict()
                ARTIFACTS[scan["run_id"]] = {"s1": scan, "s2": compare}
                return self._json({"run_id": scan["run_id"], "s1": scan, "s2": compare}, HTTPStatus.CREATED)
            if path == "/runs/discovery":
                scan = build_scan(payload).to_dict()
                compare = build_compare(scan).to_dict()
                ARTIFACTS[scan["run_id"]] = {"s1": scan, "s2": compare}
                return self._json({"run_id": scan["run_id"], "s1": scan, "s2": compare}, HTTPStatus.CREATED)
            _, _, tail = path.partition("/runs/")
            run_id, _, action = tail.partition("/")
            artifacts = ARTIFACTS[run_id]
            if action == "shortlist":
                artifacts["s3"] = build_evaluate(artifacts["s2"], payload).to_dict()
                return self._json(artifacts["s3"], HTTPStatus.CREATED)
            if action == "validate":
                artifacts["s4"] = build_validate(artifacts["s3"], payload or None).to_dict()
                return self._json(artifacts["s4"], HTTPStatus.CREATED)
            if action == "report":
                artifacts["s5"] = build_report(artifacts["s1"], artifacts.get("s2"), artifacts.get("s3"), artifacts.get("s4"))
                return self._json(artifacts["s5"], HTTPStatus.CREATED)
            raise ValueError("Unknown API route.")
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            self._json({"message": str(error)}, HTTPStatus.BAD_REQUEST)

    def _request_json(self) -> dict[str, Any]:
        size = int(self.headers.get("Content-Length", "0"))
        parsed = json.loads(self.rfile.read(size).decode("utf-8") or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("Request body must be a JSON object.")
        return parsed

    def _json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        self._json_text(json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8", status)

    def _json_text(self, payload: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8080), RadarDemoHandler)
    print("Agentic Cloud Radar demo: http://127.0.0.1:8080")
    server.serve_forever()
