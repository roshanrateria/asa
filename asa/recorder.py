"""JSONL receipt writer: every probe call leaves exactly one receipt line.

Receipt schema v0:
    {
      "v": 1,
      "ts": "<ISO-8601 UTC>",
      "run_id": "...",
      "seq": 12,
      "cell": "C12" | null,
      "transport": "rest" | "mcp-stdio" | "mcp-http",
      "tool": "create_order",
      "request": {...redacted summary, headers_of_interest...},
      "response": {"status": 201, "ids": [...], "debug_id": "...", "excerpt": "..."},
      "mock_header_used": false,
      "notes": "..."
    }

Secrets must never reach this module: call sites pass redacted summaries only
(the REST and MCP clients strip credentials before recording).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_VERSION = 1


def new_run_id(prefix: str = "run") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{stamp}-{uuid.uuid4().hex[:6]}"


@dataclass
class Recorder:
    runs_dir: str
    run_id: str
    path: Path

    def __init__(self, runs_dir: str, run_id: str | None = None) -> None:
        self.run_id = run_id or new_run_id()
        self.path = Path(runs_dir) / f"{self.run_id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.seq = 0

    def record(
        self,
        *,
        transport: str,
        tool: str,
        request: dict,
        response: dict,
        cell: str | None = None,
        mock_header_used: bool = False,
        notes: str = "",
    ) -> dict:
        self.seq += 1
        line = {
            "v": _SCHEMA_VERSION,
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "run_id": self.run_id,
            "seq": self.seq,
            "cell": cell,
            "transport": transport,
            "tool": tool,
            "request": request,
            "response": response,
            "mock_header_used": mock_header_used,
            "notes": notes,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=True) + "\n")
        return line

    def summarize(self) -> str:
        return f"{self.path} ({self.seq} receipts)"


def extract_ids(body: dict) -> list[str]:
    """Pull sandbox object ids out of a response body (best effort)."""
    if not isinstance(body, dict):
        return []
    ids = []
    for key in ("id", "order_id", "capture_id", "refund_id", "invoice_id",
                "transaction_id", "token", "links"):
        if key == "links":
            continue
        val = body.get(key)
        if isinstance(val, str) and val:
            ids.append(val)
    return ids


def excerpt_of(body: object, limit: int = 400) -> str:
    try:
        text = json.dumps(body)
    except TypeError:
        text = repr(body)
    return text[:limit]
