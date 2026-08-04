import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from log_server import run_log as run_log_module
from log_server.server import LogRequestHandler

VALID_ROW = {
    "run_id": "run-123",
    "implementation": "n8n",
    "agent": "Research Agent",
    "timestamp": "2026-08-03T14:00:00-04:00",
    "tokens_in": 1200,
    "tokens_out": 340,
    "cost_usd": 0.05,
    "latency_ms": 8210,
    "run_status": "success",
}


@pytest.fixture
def running_server():
    """Start a real ThreadingHTTPServer on an OS-assigned free port for the test."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), LogRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def post_json(address: tuple[str, int], path: str, payload: object) -> http.client.HTTPResponse:
    """POST payload as JSON to path on the running test server and return the response."""
    connection = http.client.HTTPConnection(*address)
    body = payload if isinstance(payload, (bytes, str)) else json.dumps(payload)
    connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
    return connection.getresponse()


def test_post_log_with_valid_row_returns_201_and_persists(running_server):
    response = post_json(running_server, "/log", VALID_ROW)
    assert response.status == 201
    json.loads(response.read())

    lines = run_log_module.RUN_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["run_id"] == "run-123"


def test_post_log_missing_field_returns_400_naming_it(running_server):
    incomplete_row = {k: v for k, v in VALID_ROW.items() if k != "run_id"}
    response = post_json(running_server, "/log", incomplete_row)
    assert response.status == 400
    body = json.loads(response.read())
    assert "run_id" in body["message"]


def test_post_log_malformed_json_returns_400(running_server):
    response = post_json(running_server, "/log", "not valid json")
    assert response.status == 400


def test_post_unknown_path_returns_404(running_server):
    response = post_json(running_server, "/other-path", VALID_ROW)
    assert response.status == 404
