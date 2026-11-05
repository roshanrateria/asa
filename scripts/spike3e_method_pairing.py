"""Spike 3e (2026-11-06): last refund confound - payment/refund method pairing.

Through spike3d every recorded payment was CASH; spike3c varied the refund
method only. If the refund engine validates per payment record (or per
method-match), a BANK_TRANSFER pair is the untested cell. This is also the
first refund attempt where every failed alternative has been eliminated:

  E1 create (draft, no recipient)
  E2 record_payment 5.00 method BANK_TRANSFER
  E3 record_refund 2.00 method BANK_TRANSFER   (paired)
  E4 record_refund 2.00 method CASH            (unpaired control, same invoice)

422 on both -> per-method hypothesis dead too; statement becomes: on this
sandbox date, record_refund against externally-recorded payments failed in
every reachable configuration (n>=12, receipts in runs/).
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
    rec = Recorder(cfg.runs_dir, "spike3e-method-pairing")
    rc = RestClient(cfg, rec)
    try:
        status, body, _ = rc.create_invoice(None, value="20.00",
                                            note="asa method-pairing probe",
                                            notes="spike3e E1 create")
        inv = invoice_id_of(body)
        print(f"invoice: {inv} ({status})")

        status, body, _ = rc.record_payment(inv, value="5.00", method="BANK_TRANSFER",
                                            notes="spike3e E2 pay5 BANK_TRANSFER")
        issue = None
        if isinstance(body, dict):
            details = body.get("details") or []
            issue = (details[0].get("issue") if details else None) or body.get("name")
        print(f"E2 pay 5.00 BANK_TRANSFER: {status} ({issue}) "
              f"{'payment_id=' + body.get('payment_id') if isinstance(body, dict) and body.get('payment_id') else '(rejected)'}")

        if status != 200:
            print("E2 rejected - pairing hypothesis untestable this run; receipts hold the evidence")
            return 1

        for label, method in (("E3 paired BANK_TRANSFER", "BANK_TRANSFER"),
                              ("E4 unpaired CASH", "CASH")):
            status, body, _ = rc.record_refund(inv, value="2.00", method=method,
                                               notes=f"spike3e {label}")
            issue = None
            if isinstance(body, dict):
                details = body.get("details") or []
                issue = (details[0].get("issue") if details else None) or body.get("name")
            print(f"{label}: {status} ({issue})")

        status, body, _ = rc.get_invoice(inv, notes="spike3e final state")
        print(f"final invoice status: {body.get('status') if isinstance(body, dict) else '?'}")
        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
