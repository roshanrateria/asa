"""Spike 3b (2026-11-06): refund-amount anomaly probe.

Background (spike3 v2 receipts): record_payment 5.00 -> MARKED_AS_PAID, then
record_refund 2.00 was rejected 422 INVALID_REFUND_AMOUNT ("Recorded refunds
cannot exceed recorded payments") although the numbers don't seem to violate
that invariant. This probe isolates the rule empirically on fresh invoices:

  S1  pay 5.00 -> refund 2.00   (repeat of the anomalous case)
  S2  pay 5.00 -> refund 5.00   (exact)
  S3  pay 5.00 -> refund 1.00   (smaller)
  S4  pay 5.00 -> pay 5.00      (double payment: is a second record_payment
                                 accepted after MARKED_AS_PAID?) -> refund 10.00

Every call receipted; table summarises status + invoice status after. This
seeded, repeatable sequence becomes exhibit A for the atlas.
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
    rec = Recorder(cfg.runs_dir, "spike3b-refund-anomaly")
    rc = RestClient(cfg, rec)
    rows: list[tuple[str, str, str]] = []
    try:
        def new_invoice() -> str:
            status, body, _ = rc.create_invoice(
                None, value="20.00",  # line item large enough for any scenario
                note="asa refund-anomaly probe", notes="spike3b create invoice")
            return invoice_id_of(body)

        def invoice_status(inv: str) -> str:
            status, body, _ = rc.get_invoice(inv)
            return (body.get("status") if isinstance(body, dict) else None) or f"?{status}"

        # S1 anomaly repeat
        inv = new_invoice()
        status, body, _ = rc.record_payment(inv, value="5.00", notes="spike3b S1 pay5")
        rows.append(("S1", f"pay5 {status}", invoice_status(inv)))
        status, body_, _ = rc.record_refund(inv, value="2.00", notes="spike3b S1 refund2")
        rows.append(("S1", f"refund2 {status}", invoice_status(inv)))

        # S2 exact
        inv = new_invoice()
        status, body, _ = rc.record_payment(inv, value="5.00", notes="spike3b S2 pay5")
        rows.append(("S2", f"pay5 {status}", invoice_status(inv)))
        status, body_, _ = rc.record_refund(inv, value="5.00", notes="spike3b S2 refund5")
        rows.append(("S2", f"refund5 {status}", invoice_status(inv)))

        # S3 tiny
        inv = new_invoice()
        status, body, _ = rc.record_payment(inv, value="5.00", notes="spike3b S3 pay5")
        rows.append(("S3", f"pay5 {status}", invoice_status(inv)))
        status, body_, _ = rc.record_refund(inv, value="1.00", notes="spike3b S3 refund1")
        rows.append(("S3", f"refund1 {status}", invoice_status(inv)))

        # S4 double payment then refund sum
        inv = new_invoice()
        status, body, _ = rc.record_payment(inv, value="5.00", notes="spike3b S4 pay5a")
        rows.append(("S4", f"pay5a {status}", invoice_status(inv)))
        status, body, _ = rc.record_payment(inv, value="5.00", notes="spike3b S4 pay5b")
        rows.append(("S4", f"pay5b {status}", invoice_status(inv)))
        status, body_, _ = rc.record_refund(inv, value="10.00", notes="spike3b S4 refund10")
        rows.append(("S4", f"refund10 {status}", invoice_status(inv)))

        print(f"run: {rec.summarize()}")
        print("scenario | step           | status | invoice-state-after")
        for s, step, st in rows:
            print(f"{s} | {step.ljust(14)} | {st}")
        issues = [r for r in rows if "422" in r[1]]
        if issues:
            print("refunded-422 rows above are the anomaly evidence (debug ids in receipts)")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
