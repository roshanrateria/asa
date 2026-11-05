"""Spike 3c (2026-11-06): refund failure confound isolation.

spike3b receipts: every record_refund 422'd (exact and partial), headers sent
were all null, and method was always CASH. This probe varies the two
confounds on ONE freshly paid invoice (422 leaves invoice state untouched,
so retries are clean within the same invoice):

  R1  PayPal-Request-Id injected, method CASH
  R2  id injected, method BANK_TRANSFER
  R3  id injected, method CARD
  R4  id injected, method PAYPAL
  R5  id injected, method EXTERNAL
  R6  no header, method CASH  (v-style baseline again, direct comparison)

5.00 recorded payment; every refund tried at 2.00. Uniform 422 across all six
= sandbox defect statement; mixed results = undocumented method invariant.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
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
    rec = Recorder(cfg.runs_dir, "spike3c-refund-confounds")
    rc = RestClient(cfg, rec)
    try:
        status, body, _ = rc.create_invoice(None, value="20.00",
                                            note="asa refund confound probe",
                                            notes="spike3c create")
        inv = invoice_id_of(body)
        print(f"invoice: {inv} (create {status})")

        status, body, _ = rc.record_payment(inv, value="5.00",
                                            notes="spike3c pay5")
        print(f"pay 5.00: {status}")

        rows = []
        cases = [
            ("R1", "CASH", True), ("R2", "BANK_TRANSFER", True),
            ("R3", "CARD", True), ("R4", "PAYPAL", True),
            ("R5", "EXTERNAL", True), ("R6", "CASH", False),
        ]
        for label, method, inject in cases:
            kw: dict = {"method": method}
            if inject:
                kw["headers"] = {"PayPal-Request-Id": str(uuid.uuid4())}
            status, resp, _ = rc.record_refund(inv, value="2.00",
                                               notes=f"spike3c {label} {method} "
                                                     f"header={'yes' if inject else 'no'}",
                                               **kw)
            issue = None
            if isinstance(resp, dict):
                details = resp.get("details") or []
                issue = (details[0].get("issue") if details else None) or resp.get("name")
            rows.append((label, method, inject, status, issue))

        print("case | method        | header | status | issue")
        for label, method, inject, status, issue in rows:
            print(f"{label} | {method.ljust(13)} | {'yes' if inject else 'no '} "
                  f"| {status} | {issue}")
        print(f"run: {rec.summarize()}")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
