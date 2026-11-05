"""Spike 3j (2026-11-06): verify asa's domain helpers end-to-end.

Same flow as spike3i, but exclusively through RestClient helpers, so the
harness can build on them tomorrow:

  J1 rc.create_invoice(None, "20.00")               -> 201 + extracted id
  J2 rc.record_payment 5.00 (CASH)                  -> 200, wire stores 5.00
  J3 rc.record_refund 2.00                          -> 200
  J4 rc.get_invoice final state                     -> PARTIALLY_PAID (observed)

PASS only if the wire-verified amounts reconcile.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.config import load_config
from asa.recorder import Recorder
from asa.rest_client import RestClient


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike3j-helper-roundtrip")
    rc = RestClient(cfg, rec)
    try:
        steps: list[tuple[str, bool, str]] = []

        status, body, _ = rc.create_invoice(None, "20.00",
                                            note="asa helper roundtrip",
                                            notes="J1 create via helper")
        inv = body.get("id") if isinstance(body, dict) else None
        steps.append(("J1 create_invoice (helper)", status == 201 and bool(inv), f"{status} id={inv}"))
        if not inv:
            print(f"  body: {body}")
            print("SPIKE3J: FAIL")
            return 1

        status, body, _ = rc.record_payment(inv, value="5.00",
                                            note="asa helper roundtrip",
                                            notes="J2 pay via helper")
        steps.append(("J2 record_payment (helper)", status == 200, f"{status}"))

        status, detail, _ = rc.get_invoice(inv, notes="J2b wire read")
        payments = detail.get("payments") if isinstance(detail, dict) else {}
        tx = payments.get("transactions", []) if isinstance(payments, dict) else []
        stored_ok = any((t.get("amount") or {}).get("value") == "5.00" for t in tx)
        steps.append(("J2b wire stores 5.00", stored_ok,
                      f"stored={[ (t.get('amount') or {}).get('value') for t in tx ]}"))

        status, body, _ = rc.record_refund(inv, value="2.00",
                                           notes="J3 refund via helper")
        steps.append(("J3 record_refund (helper)", status == 200, f"{status}"))

        status, detail, _ = rc.get_invoice(inv, notes="J4 final state")
        final = detail.get("status") if isinstance(detail, dict) else None
        steps.append(("J4 final status", status == 200, f"{status} invoice={final}"))

        ok = all(passed for _, passed, _ in steps)
        print(f"run: {rec.summarize()}")
        for name, passed, detail_ in steps:
            print(f"  [{'PASS' if passed else 'FAIL'}] {name} ({detail_})")
        print("SPIKE3J:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
