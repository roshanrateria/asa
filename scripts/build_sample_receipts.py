"""Build the COMMITTED sanitized receipt subset (review fix #5).

runs/*.jsonl are git-ignored but the report cites them - judges must see the
evidence. This script derives atlas/sample_receipts/, a committed subset with:

  * canonical pass1d2 rows for the headline findings (REST pair proof,
    payment pair, refund 422, echo rows, MCP masked-failure rows);
  * replay-findings rows (R1 mis-key create + read-back, R2 same-header pair,
    R3 hostile text, R4 MCP masking);
  * spike1 same-header ORDERS pair (the collapse proof vs invoicing);
  * spike4b remote-transport receipts (auth/init 404, sse silence);
  * the pinned MCP surface list (names + provenance only, no schemas).

Scrubbing (never trust the caller): recursively redacts access tokens /
bearer strings / client secrets to a length marker and normalizes sandbox
buyer emails to sb-redacted@<sandbox domain>. Tokens belong in .env only.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
OUT = ROOT / "atlas" / "sample_receipts"

EMAIL_RE = re.compile(r"[\w.+-]+@((?:personal|business)\.example\.com)")
BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]{8,}")
SECRET_KEYS = {"access_token", "client_secret", "authorization", "token",
               "refresh_token", "secret"}


def scrub(obj):
    if isinstance(obj, dict):
        return {k: (f"REDACTED(len={len(str(v))})" if k.lower() in SECRET_KEYS and v
                    else scrub(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    if isinstance(obj, str):
        s = BEARER_RE.sub(r"\1REDACTED", obj)
        return EMAIL_RE.sub(lambda m: f"sb-redacted@{m.group(1)}", s)
    return obj


def read_rows(name: str) -> list[dict]:
    path = RUNS / name
    if not path.exists():
        print(f"  !! missing {path.name} (skipped)")
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def write(name: str, payload) -> None:
    (OUT / name).write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"  + atlas/sample_receipts/{name}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. canonical harness rows --------------------------------------------
    want_rest = {2, 5, 11, 19, 82, 85, 88}
    want_mcp = {82, 88}
    def cell_of(r) -> int | None:
        try:
            return int(str(r.get("cell")))
        except (TypeError, ValueError):
            return None

    rows = read_rows("harness-pass1d2.jsonl")
    picked = [r for r in rows
              if (cell_of(r) in want_rest and r.get("transport", "rest") == "rest")
              or (cell_of(r) in want_mcp and r.get("transport") == "mcp-stdio")]
    write("harness_pass1d2_headlines.json", {
        "source": "runs/harness-pass1d2.jsonl (canonical pass, git-ignored; "
                  "full receipts local-only)",
        "derived": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scrub": "bearer/token redacted to len markers; sandbox buyer emails "
                 "normalized to sb-redacted@example domains",
        "cells_rest": sorted(want_rest), "cells_mcp": sorted(want_mcp),
        "rows": [scrub(r) for r in picked],
    })

    # 2. replay findings -----------------------------------------------------
    rows = read_rows("replay-findings.jsonl")
    write("replay_findings_rows.json", {
        "source": "runs/replay-findings.jsonl",
        "cells": "replay-r1..r4 (SF-5 mis-key create+read-back, SF-1x pair, "
                 "SF-10 hostile text, SF-9 masked failure)",
        "rows": [scrub(r) for r in rows],
    })

    # 3. spike1: same-header ORDERS pair (the honore) --------------------------
    rows = read_rows("spike1-dup-probe.jsonl")
    same = [r for r in rows
            if (r.get("request", {}).get("headers_of_interest", {})
                or {}).get("sent_paypal_request_id")]
    write("spike1_orders_same_header_pair.json", {
        "source": "runs/spike1-dup-probe.jsonl",
        "rows_picked": "every row whose SENT PayPal-Request-Id header is "
                       "receipted (orders v2 honors it: 200 return-existing, "
                       "same id, ~49 min later)",
        "rows": [scrub(r) for r in same],
    })

    # 4. spike4b remote transports --------------------------------------------
    rows = read_rows("spike4b-remote-http.jsonl")
    write("spike4b_remote_http.json", {
        "source": "runs/spike4b-remote-http.jsonl",
        "note": "/http -> 404; /sse -> stream open, zero bytes (OAuth-gated); "
                "stdio is the verified transport",
        "rows": [scrub(r) for r in rows],
    })

    # 5. pinned MCP surface (names + provenance, no schemas) -------------------
    snap = json.loads((RUNS / "mcp_tools_snapshot_stdio.json")
                      .read_text(encoding="utf-8"))
    write("mcp_tools_list_pinned_1.8.1.json", {
        "provenance": snap.get("provenance"),
        "package": "@paypal/mcp@1.8.1",
        "spawn": f"{snap.get('provenance', {}).get('spawn')}",
        "tool_count": len(snap["tools"]),
        "tools": sorted(t["name"] for t in snap["tools"]),
        "absent": ["record_payment_for_invoice", "record_refund_for_invoice"],
    })

    readm = f"""# Committed sample receipts (sanitized subset)

Generated by `scripts/build_sample_receipts.py` from the git-ignored raw runs
(`runs/*.jsonl`); the script re-derives everything below deterministically.

| file | what it evidences |
|---|---|
| `harness_pass1d2_headlines.json` | canonical pass rows: same-header create pair diverges (sent-ids proof), payment pair, refund 422, echo rows (403/stored), MCP masked-failure rows |
| `replay_findings_rows.json` | live-replayed findings R1-R4 (SF-5 zeroed amounts, SF-1x pair, SF-10 artifact, SF-9 mask) |
| `spike1_orders_same_header_pair.json` | orders v2 HONORS PayPal-Request-Id (collapse proof) - the contrast that makes the invoicing delta |
| `spike4b_remote_http.json` | remote transports closed: /http 404, /sse silent stream; stdio-only |
| `mcp_tools_list_pinned_1.8.1.json` | pinned MCP surface: 28 tools, record_* absent (D-3 precondition) |

Scrubbing: bearer/token strings redacted to length markers; sandbox buyer
emails normalized to `sb-redacted@...example.com`. Secrets live only in the
git-ignored `.env`.

The mcp tools subset here is intentionally schema-free; the full schema dump
is `runs/mcp_tools_snapshot_stdio.json` (git-ignored).
"""
    (OUT / "README.md").write_text(readm, encoding="utf-8")
    print("  + atlas/sample_receipts/README.md")
    print("SUBSET-RECEIPTS: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
