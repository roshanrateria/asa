"""Spike 3h (2026-11-06): amount-due ground truth on the wire.

spike3g: paying with the 'amount' field shape got 422
PAYMENT_AMOUNT_GREATER_THAN_AMOUNT_DUE for 5.00 against a 20.00 line item.
Hypothesis: the invoice's amount due is actually 0.00 on the wire, which
would explain BOTH the payment deadlock and the zero-amount store.

  H1 GET the spike3g invoice -> print all amount fields on the wire
  H2 fresh create (control) -> GET -> print amount fields too
  H3 on the fresh invoice: 'amount' field 5.00, then 0.01 -> statuses

Every step receipted. This is the last refund-surface probe tonight; after
it the findings go into docs/evidence.md and the matrix gets its justified
prune rules.
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


def amount_snapshot(detail: dict) -> dict:
    """Extract every amount-ish field the wire returns."""
    interesting = {}
    if not isinstance(detail, dict):
        return interesting
    for key in ("amount", "summary", "due_amount", "amount_due"):
        val = detail.get(key)
        if val is not None:
            interesting[key] = val
    if isinstance(detail.get("amount"), dict):
        pass
    return interesting


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike3h-amount-due")
    rc = RestClient(cfg, rec)
    try:
        print("== H1: the spike3g invoice, as stored ==")
        status, detail, _ = rc.get_invoice("INV2-DUG6-XN6Q-29CL-5X47",
                                           notes="spike3h H1 read")
        print(json.dumps({"status": detail.get("status"),
                          "amount_fields": amount_snapshot(detail)} if isinstance(detail, dict) else detail,
                         indent=2)[:900])

        print("== H2: fresh control invoice ==")
        status, body, _ = rc.create_invoice(None, value="20.00",
                                            note="asa amount-due probe",
                                            notes="spike3h H2 create")
        inv = invoice_id_of(body)
        status, detail, _ = rc.get_invoice(inv, notes="spike3h H2 read fresh")
        print(json.dumps({"id": inv, "status": detail.get("status"),
                          "amount_fields": amount_snapshot(detail)} if isinstance(detail, dict) else detail,
                         indent=2)[:1200])

        print("== H3: amount-field payment attempts on the fresh invoice ==")
        for value, label in (("5.00", "attempt 5.00"), ("0.01", "attempt 0.01")):
            body_p = {"method": "CASH",
                      "amount": {"currency_code": "USD", "value": value},
                      "note": "asa amount-due probe"}
            status, resp, _ = rc.call(
                "POST", f"/v2/invoicing/invoices/{inv}/payments", json=body_p,
                notes=f"spike3h {label} 'amount' field")
            issue = None
            if isinstance(resp, dict):
                details = resp.get("details") or []
                issue = (details[0].get("issue") if details else None) or resp.get("name")
            print(f"{label}: {status} ({issue})")

        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
