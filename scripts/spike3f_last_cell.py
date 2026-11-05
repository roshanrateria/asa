"""Spike 3f (2026-11-06): last confound cell + ground truth read.

Grid cells eliminated so far (all 422): draft/sent, amounts 1-10 (<= payment),
refund methods CASH/BANK_TRANSFER/PAYPAL, header/no-header, per-method pairing
(spike3b/3c/3d/3e receipts, n=13).

This run closes the grid with the remaining cell and reads back the invoice
detail so the recorded payment's own fields are on the record:

  F1 create (draft)
  F2 record_payment 5.00, method PAYPAL
  F3 record_refund 2.00 method PAYPAL   (same-method pair, last cell)
  F4 GET invoice -> dump the payments array from the wire
  F5 record_refund 2.00 method CASH     (control)

If F4 shows amount 5.00 stored while F3/F5 still 422 -> refund-side engine
defect; if F4 shows wrong stored amount -> payment-recording side defect.
Either way the atlas entry gets its localization.
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
    rec = Recorder(cfg.runs_dir, "spike3f-last-cell")
    rc = RestClient(cfg, rec)
    try:
        status, body, _ = rc.create_invoice(None, value="20.00",
                                            note="asa last refund cell",
                                            notes="spike3f F1 create")
        inv = invoice_id_of(body)
        print(f"invoice: {inv} ({status})")

        status, body, _ = rc.record_payment(inv, value="5.00", method="PAYPAL",
                                            notes="spike3f F2 pay5 PAYPAL")
        pid = body.get("payment_id") if isinstance(body, dict) else None
        print(f"F2 pay 5.00 PAYPAL: {status} payment_id={pid}")

        if status == 200:
            for label, method in (("F3 refund2 PAYPAL", "PAYPAL"),
                                  ("F5 refund2 CASH", "CASH")):
                status, body, _ = rc.record_refund(inv, value="2.00", method=method,
                                                   notes=f"spike3f {label}")
                issue = None
                if isinstance(body, dict):
                    details = body.get("details") or []
                    issue = (details[0].get("issue") if details else None) or body.get("name")
                print(f"{label}: {status} ({issue})")

            status, body, _ = rc.get_invoice(inv, notes="spike3f F4 wire read")
            payments = body.get("payments") if isinstance(body, dict) else None
            print("F4 wire read: invoice payments array =")
            print(json.dumps(payments, indent=2)[:800])
            print(f"final invoice status: {body.get('status') if isinstance(body, dict) else '?'}")
        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
