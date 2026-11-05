"""Spike 2 (2026-11-06): the money path - the critical gate (E7 risk 1).

Question: can this harness capture a payment programmatically on the sandbox?

Path A (card): create a CAPTURE order funded by a sandbox test card
               (ASA_CARD_PAN / EXPIRY / CVV in .env, numbers from the official
               card-testing page), then capture, then refund - no buyer UI.
Path B (wallet): buyer approval is a sandbox.paypal.com UI action [V-1105],
               therefore OUT of programmatic reach; this script does not
               attempt it and records that as a note instead.

PASS  -> the order family stays in matrix scope.
FAIL  -> invoice-only slice (spike 3 record_payment/record_refund carry the
         money semantics), per blueprint fallback E8-1.

Set the card env vars in .env first; without them this prints instructions
and exits 0 without attempting anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.config import load_config
from asa.recorder import Recorder
from asa.rest_client import RestClient

CARD_TESTING_URL = "https://developer.paypal.com/sandbox-testing/card-testing#test-card-numbers"


def main() -> int:
    cfg = load_config()

    if not (cfg.card_pan and cfg.card_expiry and cfg.card_cvv):
        print("SPIKE2: SKIPPED - no card env vars.")
        print(f"  Get a sandbox test card number from: {CARD_TESTING_URL}")
        print("  Fill ASA_CARD_PAN / ASA_CARD_EXPIRY / ASA_CARD_CVV in .env, rerun.")
        return 0

    rec = Recorder(cfg.runs_dir, "spike2-money-path")
    rc = RestClient(cfg, rec)
    try:
        # Expiry format is not pinned by the local docs (ledger unknown C):
        # try as given, then the Orders v2 style YYYY-MM, and optionally a
        # cardholder name. Four attempts max; every attempt is receipted.
        expiry_variants = [cfg.card_expiry]
        if cfg.card_expiry and "/" in cfg.card_expiry:
            mm, yyyy = cfg.card_expiry.split("/", 1)
            expiry_variants.append(f"{yyyy}-{mm}")
        attempts = [(exp, extra) for exp in expiry_variants
                    for extra in ({}, {"name": "ASA AUDIT PROBE"})][:4]

        order_id = None
        card_used = None
        status, body = 0, None
        for exp, extra in attempts:
            card = {"number": cfg.card_pan, "expiry": exp, "cvv": cfg.card_cvv, **extra}
            status, body, meta = rc.create_order(
                "5.00", card=card, inject_request_id=True,
                notes=f"spike2 card-funded order (expiry={exp}, name={'yes' if extra else 'no'})")
            print(f"create_order attempt (expiry={exp}, cardholder_name={bool(extra)}): "
                  f"{status} id={body.get('id') if isinstance(body, dict) else None}")
            if status == 201 and isinstance(body, dict) and body.get("id"):
                order_id = body["id"]
                card_used = (exp, bool(extra))
                break
        if not order_id:
            print(f"  last body: {body}")
            print("SPIKE2: FAIL at create_order -> invoice-only slice fallback")
            return 1

        status, body, meta = rc.capture_order(order_id, notes="spike2 capture")
        print(f"capture: {status}")
        capture_id = None
        if isinstance(body, dict):
            for pu in body.get("purchase_units", []):
                for captured in pu.get("payments", {}).get("captures", []):
                    capture_id = captured.get("id")
        if status not in (200, 201) or not capture_id:
            print(f"  body: {body}")
            print("SPIKE2: FAIL at capture -> invoice-only slice fallback")
            return 1

        status, body, meta = rc.refund_capture(capture_id, value="2.00",
                                               notes="spike2 partial refund")
        print(f"refund: {status}")
        if isinstance(body, dict):
            print(f"  refund id: {body.get('id')}")

        print(f"run: {rec.summarize()}")
        print("SPIKE2: PASS - order family stays in matrix scope")
        return 0
    finally:
        rc.close()


if __name__ == "__main__":
    raise SystemExit(main())
