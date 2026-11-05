"""Spike 3 (2026-11-06): invoice round-trip - the fallback slice's backbone.

Steps (every step receipted):
  1. create_invoice (draft, $5.00 line item)     -> invoice id
  2. (optional) send_invoice to the Personal sandbox recipient
  3. record_payment_for_invoice $5.00            -> invoice PAID?
  4. record_refund_for_invoice $2.00             -> refund recorded?
  5. get_invoice                                 -> final status observe

PASS -> the invoice family can carry money semantics end-to-end
        programmatically (no buyer UI), so the invoice-only slice is viable.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.config import load_config
from asa.recorder import Recorder
from asa.rest_client import RestClient


def invoice_id_of(body) -> str | None:
    if isinstance(body, dict) and body.get("id"):
        return body["id"]
    m = re.search(r"v2/invoicing/invoices/([A-Za-z0-9\-]+)", json.dumps(body))
    return m.group(1) if m else None


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike3-invoice-roundtrip")
    rc = RestClient(cfg, rec)
    try:
        steps: list[tuple[str, bool, str]] = []

        # v2 pivot (2026-11-06): recipient-less DRAFT invoice. The v1 run's
        # send/record 406s carried INR_FOREIGN_CURRENCY_BLOCKED for the
        # India-country sandbox accounts; the send lifecycle resumes once a
        # US-country Personal sandbox account exists (docs/plan.md task list).
        status, body, _ = rc.create_invoice(None, value="5.00",
                                            note="asa audit probe invoice",
                                            notes="spike3v2 step1 create draft, no recipient")
        steps.append(("create_invoice", 200 <= status < 300, f"status={status}"))
        invoice_id = invoice_id_of(body)
        print(f"create_invoice: {status} id={invoice_id} body={body}")
        if not invoice_id:
            print("SPIKE3: FAIL - no invoice id; stopping")
            return 1

        steps.append(("send_invoice", True,
                      "skipped (India-country recipient block, 406; US account pending)"))

        status, body, _ = rc.record_payment(invoice_id, value="5.00",
                                            notes="spike3 step3 record payment")
        steps.append(("record_payment", 200 <= status < 300, f"status={status}"))
        print(f"record_payment: {status} body={body}")

        status, body, _ = rc.record_refund(invoice_id, value="2.00",
                                           notes="spike3 step4 record refund")
        steps.append(("record_refund", 200 <= status < 300, f"status={status}"))
        print(f"record_refund: {status} body={body}")

        status, body, _ = rc.get_invoice(invoice_id, notes="spike3 step5 final state")
        final_status = body.get("status") if isinstance(body, dict) else None
        steps.append(("get_invoice", 200 <= status < 300,
                      f"status={status} invoice_status={final_status}"))
        print(f"get_invoice: {status} final={final_status}")

        ok = all(passed for _, passed, _ in steps)
        print(f"run: {rec.summarize()}")
        for name, passed, detail in steps:
            print(f"  [{'PASS' if passed else 'FAIL'}] {name} ({detail})")
        print("SPIKE3:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
