"""Spike 3i (2026-11-06): items-key fix probe - the full invoice family re-run.

spike3h annotated the root cause: create_invoice accepted our body that used
'line_items' (wrong key; v2 uses 'items') and SILENTLY DROPPED it, storing
due_amount 0.00 - a $20 invoice stored as a $0 object, valid per its status.

This probe reruns the round trip with 'items':

  I1 create with items (20.00)   -> expect due_amount 20.00 on wire
  I2 record_payment 5.00 ('amount' field; fall back to 'payment_amount')
  I3 wire read (paid 5.00?)
  I4 record_refund 2.00
  I5 final status: PAID->PARTIALLY_REFUNDED expected

If I4 returns 200 the invoice REFUND cells are LIVE again and tonight's
earlier 422s re-tag as consequences of the silent-drop, not an engine defect.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
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


def issue_of(resp) -> str | None:
    if isinstance(resp, dict):
        details = resp.get("details") or []
        return (details[0].get("issue") if details else None) or resp.get("name")
    return None


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike3i-items-fix")
    rc = RestClient(cfg, rec)
    try:
        create_body = {
            "detail": {"currency_code": "USD",
                       "note": "asa items-key probe"},
            "items": [{
                "name": "audit probe item",
                "unit_amount": {"currency_code": "USD", "value": "20.00"},
                "quantity": "1",
            }],
        }
        status, body, _ = rc.call("POST", "/v2/invoicing/invoices", json=create_body,
                                  notes="spike3i I1 create with 'items'")
        inv = invoice_id_of(body)
        print(f"I1 create with items: {status} id={inv}")

        status, detail, _ = rc.get_invoice(inv, notes="spike3i I1b wire read")
        amount = detail.get("amount") if isinstance(detail, dict) else None
        due = detail.get("due_amount") if isinstance(detail, dict) else None
        amt_val = amount.get("value") if isinstance(amount, dict) else None
        due_val = due.get("value") if isinstance(due, dict) else None
        print(f"I1b wire: amount.value={amt_val} due_amount.value={due_val}")

        if due_val != "20.00":
            print("  due still not 20.00 - 'items' key rejected too; printing items:")
            items = detail.get("items") if isinstance(detail, dict) else None
            print(json.dumps(items, indent=2)[:600])
            print(f"run: {rec.summarize()}")
            return 1

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        pay_body = {"method": "CASH",
                    "amount": {"currency_code": "USD", "value": "5.00"},
                    "payment_date": today,
                    "note": "asa items-key probe"}
        status, resp, _ = rc.call("POST", f"/v2/invoicing/invoices/{inv}/payments",
                                  json=pay_body, notes="spike3i I2 pay 'amount'")
        print(f"I2 pay via 'amount': {status} ({issue_of(resp)})")
        if status // 100 != 2:
            pay_body = {"payment_amount": {"currency_code": "USD", "value": "5.00"},
                        "method": "CASH", "payment_date": today}
            status, resp, _ = rc.call("POST", f"/v2/invoicing/invoices/{inv}/payments",
                                      json=pay_body, notes="spike3i I2b pay 'payment_amount'")
            print(f"I2b pay via 'payment_amount': {status} ({issue_of(resp)})")

        status, detail, _ = rc.get_invoice(inv, notes="spike3i I3 wire read after pay")
        payments = detail.get("payments") if isinstance(detail, dict) else {}
        tx = payments.get("transactions", []) if isinstance(payments, dict) else []
        stored = [t.get("amount", {}).get("value") for t in tx]
        print(f"I3 stored payment amounts: {stored} status={detail.get('status')}")

        status, resp, _ = rc.record_refund(inv, value="2.00",
                                           notes="spike3i I4 refund 2.00")
        print(f"I4 refund 2.00: {status} ({issue_of(resp)})")

        status, detail, _ = rc.get_invoice(inv, notes="spike3i I5 final")
        print(f"I5 final invoice status: {detail.get('status') if isinstance(detail, dict) else '?'}")
        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
