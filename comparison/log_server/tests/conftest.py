import pytest

from log_server import run_log as run_log_module


@pytest.fixture(autouse=True)
def isolate_run_log_path(tmp_path, monkeypatch):
    """Redirect the shared run-log file to a throwaway path for every test."""
    monkeypatch.setattr(run_log_module, "RUN_LOG_PATH", tmp_path / "run_logs" / "run_logs.jsonl")
