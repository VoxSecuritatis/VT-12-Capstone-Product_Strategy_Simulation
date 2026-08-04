# log_server

Local HTTP endpoint for this capstone -- exposes `POST /log`, which validates one JSON run-log
row against the shared schema and appends it to `comparison/run_logs/run_logs.jsonl`. n8n's HTTP
Request node calls this once per agent node; the future CrewAI implementation will write to the
same file. See the top-level `README.md` and `SETUP.md` for the full design.

## Quick start

```bash
uv run log-server        # starts the server on http://127.0.0.1:8100 (POST /log)
uv run pytest             # runs the test suite
```

No `.env` values required -- override `LOG_SERVER_HOST` / `LOG_SERVER_PORT` as shell env vars if
the defaults ever conflict with something else running locally.
