"""Spike 1 (2026-11-06): duplicate-effect probe for ledger unknown B.

Question: does the sandbox REST edge actually pay attention to
PayPal-Request-Id, and what does a bare retry do? This is the REST-side
ground truth the matrix's RETRY_* call shapes rely on.

Design: three pairs of identical create_order("2.50") calls:
  A  fresh id each time        -> expect two DIFFERENT order ids
  B  same PayPal-Request-Id    -> expect ONE order id (or duplicate keys)
  C  no header at all          -> docs claim duplicates [V-1101]; measure it

No capture, no approval - cheap and disposable. Prints a verdict table and
writes receipts. Answers update docs/evidence.md unknown B.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.config import load_config
from asa.recorder import Recorder
from asa.rest_client import RestClient


def order_id_of(body) -> str | None:
    if isinstance(body, dict):
        return body.get("id")
    return None


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike1-dup-probe")
    rc = RestClient(cfg, rec)
    try:
        results: list[tuple[str, str | None, str | None]] = []
        for label, make_headers in (
            ("A_fresh_ids", lambda i: {"PayPal-Request-Id": str(uuid.uuid4())}),
            ("B_same_id", lambda i: {"PayPal-Request-Id": "asa-spike1-fixed"}),
            ("C_no_header", lambda i: None),
        ):
            ids: list[str | None] = []
            for i in (0, 1):
                headers = make_headers(i)
                status, body, meta = rc.call(
                    "POST", "/v2/checkout/orders",
                    json={"intent": "CAPTURE",
                          "purchase_units": [{"amount": {"currency_code": "USD",
                                                          "value": "2.50"}}]},
                    headers=headers,
                    notes=f"spike1 {label} call{i}",
                )
                ids.append(order_id_of(body))
            results.append((label, ids[0], ids[1]))

        print(f"run: {rec.summarize()}")
        for label, a, b in results:
            dup = (a == b) if (a is not None and b is not None) else None
            print(f"  {label}: {a} / {b}  duplicate={dup}")
        print("SPIKE1: recorded (see receipt lines for statuses)")
    finally:
        rc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
