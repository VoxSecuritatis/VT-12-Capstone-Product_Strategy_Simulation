# ================================================================
# Run-Log HTTP Server Entrypoint
# ================================================================
# Objective:
#       Serve one local HTTP endpoint, POST /log, that n8n's HTTP Request
#       node calls once per agent node so run-log rows land in the shared
#       comparison/run_logs/run_logs.jsonl file that Phase 5's compare.py
#       reads from both implementations.
# Inputs:
#       - LOG_SERVER_HOST / LOG_SERVER_PORT (optional, env; defaults
#         127.0.0.1:8100)
#       - POST body: one JSON object per the shared run-log schema
# Outputs:
#       - a running HTTP server; each valid POST appends one line to
#         run_logs.jsonl
# Notes:
#   - stdlib only (http.server.ThreadingHTTPServer) -- no framework
#     dependency needed for one endpoint that validates and appends a
#     line to a file.
# ================================================================

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from log_server.run_log import InvalidRunLogRow, append_run_log_row, validate_run_log_row

LOG_PATH = "/log"


class LogRequestHandler(BaseHTTPRequestHandler):
    """Handles POST /log by validating and appending one run-log row."""

    def do_POST(self) -> None:
        """Validate the POSTed run-log row and append it, or return an error."""
        if self.path != LOG_PATH:
            self.send_error_response(404, "not found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.log_message("[WARN] rejected malformed JSON body")
            self.send_error_response(400, "request body is not valid JSON")
            return

        try:
            row = validate_run_log_row(data)
        except InvalidRunLogRow as exc:
            self.log_message(f"[WARN] rejected invalid run-log row: {exc}")
            self.send_error_response(400, str(exc))
            return

        append_run_log_row(row)
        self.log_message(f"[INFO] logged {row['agent']} for run {row['run_id']}")
        self.send_json_response(201, {"status": "ok"})

    def send_json_response(self, status: int, payload: dict) -> None:
        """Write a JSON response with the given status code."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_response(self, status: int, message: str) -> None:
        """Write a JSON error response with the given status code."""
        self.send_json_response(status, {"status": "error", "message": message})

    def log_message(self, fmt: str, *args: object) -> None:
        """Replace stdlib's default access log with the project's [INFO]/[WARN] convention."""
        print(fmt % args if args else fmt)


def main() -> None:
    """Run the run-log HTTP server until interrupted."""
    host = os.environ.get("LOG_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("LOG_SERVER_PORT", "8100"))
    server = ThreadingHTTPServer((host, port), LogRequestHandler)
    print(f"[INFO] log_server listening on http://{host}:{port}{LOG_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[INFO] log_server shutting down")


if __name__ == "__main__":
    main()
