"""Spike 0 (2026-11-06): credentials, token, and two cheap read calls.

PASS criteria (decision evidence for gate G-SPIKE):
  1. OAuth token mint succeeds.
  2. GET /v2/invoicing/invoices returns 200.
  3. GET /v1/reporting/transactions returns 200.

Every call is recorded as a JSONL receipt under runs/.
Date format for /v1/reporting/transactions is TODO-verify-at-spike; a format
rejection is itself recorded and adjusted once.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.config import load_config
from asa.recorder import Recorder
from asa.rest_client import RestClient


def fmt(dt: datetime) -> str:
    # common sandbox-accepted style; adjust once if rejected
    return dt.strftime("%Y-%m-%dT%H:%M:%S-0000")


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike0-smoke")
    rc = RestClient(cfg, rec)

    verdict: list[tuple[str, bool, str]] = []
    try:
        status, body, _ = rc.call("GET", "/v2/invoicing/invoices",
                                  params={"page_size": 10, "page": 1, "total_required": True})
        verdict.append(("list_invoices", status == 200, f"status={status}"))
        if status != 200:
            print(f"invoices body: {body}")

        now = datetime.now(timezone.utc)
        status, body, _ = rc.list_transactions(fmt(now - timedelta(days=10)), fmt(now))
        verdict.append(("list_transactions", status == 200, f"status={status}"))
        if status != 200:
            print(f"transactions body: {body}")

        # prove token minting worked implicitly ( RestClient would have raised )
        verdict.insert(0, ("oauth_token", True, "minted"))
    finally:
        rc.close()

    ok = True
    print(f"run: {rec.summarize()}")
    for name, passed, detail in verdict:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name} ({detail})")
        ok = ok and passed
    print("SPIKE0:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
