"""Spike 3d (2026-11-06): does record_refund need a SENT invoice?

Confound left after spikes 3b/3c: every successful record_payment happened on
a recipient-LESS DRAFT invoice, and every record_refund failed. Maybe the
refund engine only validates against payments on a SENT invoice. The v1 run
blocked sending at 406 INR_FOREIGN_CURRENCY_BLOCKED because the default
Personal sandbox account is India-country (recipient-side wording).

Test: RFC-2606 reserved address example.com (IANA placeholder - reaches no
mailbox) as the recipient, so the send lifecycle runs without a new sandbox
account and without emailing any real person.

  D1 create invoice WITH recipient invoice-test@example.com
  D2 send_invoice            -> if 406 again, the block is sender-side
  D3 record_payment 5.00
  D4 record_refund 2.00      -> the one that should succeed if SENT is the blocker

Every step receipted; ends with the final invoice status.
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

RECIPIENT = "invoice-test@example.com"   # IANA RESERVED domain - no real mailbox


def invoice_id_of(body) -> str | None:
    if isinstance(body, dict) and body.get("id"):
        return body["id"]
    m = re.search(r"v2/invoicing/invoices/([A-Za-z0-9\-]+)", json.dumps(body))
    return m.group(1) if m else None


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike3d-sent-refund")
    rc = RestClient(cfg, rec)
    try:
        status, body, _ = rc.create_invoice(RECIPIENT, value="20.00",
                                            note="asa sent-state refund probe",
                                            notes="spike3d D1 create with recipient")
        print(f"D1 create: {status}")
        inv = invoice_id_of(body)
        if not inv:
            print(f"  body: {body}")
            return 1

        status, body, _ = rc.send_invoice(inv, RECIPIENT, notes="spike3d D2 send")
        print(f"D2 send: {status} {body if status >= 400 else ''}")
        if status >= 400:
            print("  -> block looks sender-side; refund needs a US-country account")

        status, body, _ = rc.record_payment(inv, value="5.00", notes="spike3d D3 pay5")
        print(f"D3 pay 5.00: {status}")

        status, body, _ = rc.record_refund(inv, value="2.00", notes="spike3d D4 refund2")
        issue = None
        if isinstance(body, dict):
            details = body.get("details") or []
            issue = (details[0].get("issue") if details else None) or body.get("name")
        print(f"D4 refund 2.00: {status} ({issue})")

        status, body, _ = rc.get_invoice(inv, notes="spike3d final state")
        final = body.get("status") if isinstance(body, dict) else None
        print(f"final invoice status: {final}")
        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
