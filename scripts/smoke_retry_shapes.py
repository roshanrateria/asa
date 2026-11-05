"""Pre-flight smoke for pass 1c: do the retry shapes actually send their header policy?

Three pairs of create calls:
  SAME -> two calls, one fixed PayPal-Request-Id
  NONE -> two calls, header absent
  FRESH -> two calls, fresh ids
Prints sent/echoed ids + returned ids per call through rc.call receipts.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.config import load_config
from asa.recorder import Recorder, extract_ids
from asa.rest_client import RestClient


def body():
    return {"detail": {"currency_code": "USD"},
            "items": [{"name": "asa smoke item",
                       "unit_amount": {"currency_code": "USD", "value": "5.00"},
                       "quantity": "1"}]}


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "smoke-retry-shapes")
    rc = RestClient(cfg, rec)
    fixed = str(uuid.uuid4())
    try:
        for shape in ("RETRY_SAME_REQUEST_ID", "RETRY_NO_REQUEST_ID", "FRESH"):
            ids_sent: list[str | None] = []
            for i in range(2):
                headers = ({"PayPal-Request-Id": fixed}
                           if shape == "RETRY_SAME_REQUEST_ID"
                           else None if shape == "RETRY_NO_REQUEST_ID"
                           else {"PayPal-Request-Id": str(uuid.uuid4())})
                status, resp, meta = rc.call(
                    "POST", "/v2/invoicing/invoices", json=body(), headers=headers,
                    cell=f"smoke-{shape}", notes=f"{shape} #{i}")
                ids_sent.append(meta["sent_paypal_request_id"])
                got = extract_ids(resp) if isinstance(resp, dict) else []
                print(f"{shape} #{i}: sent={ids_sent[i]} status={status} ids={got}")
            label = ("same" if shape == "RETRY_SAME_REQUEST_ID"
                     else "none" if shape == "RETRY_NO_REQUEST_ID" else "fresh")
            print(f"-> {label}: sent_unique={len(set(map(str, ids_sent)))}")
    finally:
        rc.close()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
