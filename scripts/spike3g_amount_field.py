"""Spike 3g (2026-11-06): record_payment amount-field probe.

Evidence so far (spike3f): record_payment 5.00 -> 200 + payment_id; invoice
MARKED_AS_PAID; but the wire reads the stored transaction amount as 0.00 and
paid_amount 0.00. Every record_refund (n=13) then 422s with
INVALID_REFUND_AMOUNT - arithmetically true against a zero stored payment.

Question: is the amount lost because the body field is wrong? v1 sent
{"payment_amount": {...}(+"method")}. This probe sends the
alternative surface used by invoicing docs' payment records:

  G1 create invoice (draft, 20.00 line item)
  G2 record payment with {"method": "CASH", "amount": {...5.00...},
     "payment_date", "note"}
  G3 GET wire read of the stored transaction
  G4 if amount stored 5.00 -> record_refund 2.00 -> final status

Outcome A: amount stored -> field-name finding: "amount" is the operative
field; wrongly-named amount silently stores 0.00 (silent-descaling write).
Outcome B: still 0.00 -> payment-recording side stores zero regardless;
defect statement stands, localized at /payments.
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


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike3g-amount-field")
    rc = RestClient(cfg, rec)
    try:
        status, body, _ = rc.create_invoice(None, value="20.00",
                                            note="asa amount-field probe",
                                            notes="spike3g G1 create")
        inv = invoice_id_of(body)
        print(f"invoice: {inv} ({status})")

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        body_g2 = {
            "method": "CASH",
            "amount": {"currency_code": "USD", "value": "5.00"},
            "payment_date": today,
            "note": "asa amount-field probe",
        }
        status, resp, _ = rc.call(
            "POST", f"/v2/invoicing/invoices/{inv}/payments", json=body_g2,
            notes="spike3g G2 pay 'amount' field")
        print(f"G2 pay via 'amount' field: {status} "
              f"payment_id={resp.get('payment_id') if isinstance(resp, dict) else None}")

        status, detail, _ = rc.get_invoice(inv, notes="spike3g G3 wire read")
        payments = detail.get("payments") if isinstance(detail, dict) else None
        tx = (payments or {}).get("transactions", [])
        stored = [t.get("amount", {}).get("value") for t in tx]
        print(f"G3 stored amounts on wire: {stored}")
        print(f"   paid_amount: {(payments or {}).get('paid_amount')}")
        print(f"   invoice status: {detail.get('status') if isinstance(detail, dict) else '?'}")

        if stored and len(stored) and stored[-1] not in (None, "0.00"):
            status, resp, _ = rc.record_refund(inv, value="2.00",
                                               notes="spike3g G4 refund with stored 5.00")
            issue = None
            if isinstance(resp, dict):
                details = resp.get("details") or []
                issue = (details[0].get("issue") if details else None) or resp.get("name")
            print(f"G4 refund 2.00: {status} ({issue})")
            status, detail, _ = rc.get_invoice(inv, notes="spike3g final")
            print(f"   final status: {detail.get('status') if isinstance(detail, dict) else '?'}")
        else:
            print("G4 skipped - amount still not stored; defect sits at /payments regardless of field name")

        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
