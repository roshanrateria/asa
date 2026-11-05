"""Sandbox REST client with PayPal-Request-Id experiment hooks.

Endpoints used (to be re-verified against the live API reference during the
spike; every call is recorded with status + debug_id either way):

  token           POST /v1/oauth2/token
  create_order    POST /v2/checkout/orders
  capture         POST /v2/checkout/orders/{id}/capture
  get_order       GET  /v2/checkout/orders/{id}
  refund capture  POST /v2/payments/captures/{id}/refund
  get_refund      GET  /v2/payments/refunds/{id}
  transactions    GET  /v1/reporting/transactions
  create_invoice  POST /v2/invoicing/invoices
  get_invoice     GET  /v2/invoicing/invoices/{id}
  send_invoice    POST /v2/invoicing/invoices/{id}/send
  record payment  POST /v2/invoicing/invoices/{id}/payments
  record refund   POST /v2/invoicing/invoices/{id}/refunds

Experiment hooks (ledger unknown B):
  * inject_request_id: attach a fresh PayPal-Request-Id (uuid4)
  * explicit header passthrough for retry probes (same id twice / no id)
"""

from __future__ import annotations

import base64
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from asa.config import Config
from asa.recorder import Recorder, excerpt_of, extract_ids

TOKEN_PATH = "/v1/oauth2/token"


class RestClient:
    def __init__(self, cfg: Config, recorder: Recorder | None = None) -> None:
        self.cfg = cfg
        self.rec = recorder
        self._client = httpx.Client(base_url=cfg.api_base, timeout=30.0)
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # -- auth ---------------------------------------------------------------
    def _token_fetch(self) -> str:
        raw = f"{self.cfg.client_id}:{self.cfg.client_secret}".encode()
        basic = base64.b64encode(raw).decode()
        resp = self._client.post(
            TOKEN_PATH,
            headers={
                "Authorization": f"Basic {basic}",
                "Accept": "application/json",
            },
            data={"grant_type": "client_credentials"},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"token fetch failed: {resp.status_code} {resp.text[:200]}")
        body = resp.json()
        self._token = body["access_token"]
        # tokens live 3-8 h; refresh with 60 s slack
        self._token_expiry = time.time() + int(body.get("expires_in", 3600)) - 60
        return self._token

    def _auth_header(self) -> str:
        if self._token is None or time.time() >= self._token_expiry:
            self._token_fetch()
        assert self._token is not None
        return f"Bearer {self._token}"

    def close(self) -> None:
        self._client.close()

    # -- generic call -------------------------------------------------------
    def call(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        inject_request_id: bool = False,
        cell: str | None = None,
        mock_response_code: str | None = None,
        notes: str = "",
    ) -> tuple[int, Any, dict]:
        """One HTTP exchange; returns (status, body, headers_of_interest).

        headers_of_interest carries PayPal-Request-Id (if echoed), debug_id,
        and the record of what we sent.
        """
        hdrs = {"Authorization": self._auth_header(), "Accept": "application/json"}
        sent_request_id: str | None = None
        if headers:
            hdrs.update(headers)
            sent_request_id = headers.get("PayPal-Request-Id")
        elif inject_request_id:
            sent_request_id = str(uuid.uuid4())
            hdrs["PayPal-Request-Id"] = sent_request_id

        mock_used = False
        if mock_response_code is not None:
            # Sandbox-only documented affordance (negative testing).
            hdrs["PayPal-Mock-Response"] = json_dumps(
                {"mock_application_codes": mock_response_code})
            mock_used = True
        if json is not None:
            hdrs["Content-Type"] = "application/json"

        resp = self._client.request(method, path, json=json, params=params, headers=hdrs)
        try:
            body: Any = resp.json()
        except Exception:
            body = resp.text

        interesting = {
            "sent_paypal_request_id": sent_request_id,
            "echoed_paypal_request_id": resp.headers.get("PayPal-Request-Id"),
            "debug_id": body.get("debug_id") if isinstance(body, dict) else None,
            "mock_header_used": mock_used,
        }

        if self.rec is not None:
            self.rec.record(
                transport="rest",
                tool=path,
                request={"method": method, "params": params, "json": json,
                         "headers_of_interest": interesting},
                response={"status": resp.status_code,
                          "ids": extract_ids(body) if isinstance(body, dict) else [],
                          "debug_id": interesting["debug_id"],
                          "excerpt": excerpt_of(body)},
                cell=cell,
                mock_header_used=mock_used,
                notes=notes,
            )
        return resp.status_code, body, interesting

    # -- domain helpers (thin, amounts as strings per PayPal wire format) ----
    def create_order(self, value: str, currency: str = "USD",
                     *, card: dict | None = None, **kw) -> tuple[int, Any, dict]:
        # NOTE(spike-verify): exact placement of payment_source.card in the
        # Orders v2 body is verified live during spike 2; a documented failure
        # mode here is itself a receipt.
        body: dict = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": currency, "value": value},
            }],
        }
        if card is not None:
            body["payment_source"] = {"card": card}
        return self.call("POST", "/v2/checkout/orders", json=body, **kw)

    def capture_order(self, order_id: str, **kw) -> tuple[int, Any, dict]:
        return self.call("POST", f"/v2/checkout/orders/{order_id}/capture", **kw)

    def get_order(self, order_id: str, **kw) -> tuple[int, Any, dict]:
        return self.call("GET", f"/v2/checkout/orders/{order_id}", **kw)

    def refund_capture(self, capture_id: str, value: str | None = None,
                       currency: str = "USD", **kw) -> tuple[int, Any, dict]:
        json_body = None
        if value is not None:
            json_body = {"amount": {"currency_code": currency, "value": value}}
        return self.call("POST", f"/v2/payments/captures/{capture_id}/refund",
                         json=json_body, **kw)

    def list_transactions(self, start_iso: str, end_iso: str, **kw) -> tuple[int, Any, dict]:
        return self.call("GET", "/v1/reporting/transactions",
                         params={"start_date": start_iso, "end_date": end_iso,
                                 "fields": "all"}, **kw)

    def create_invoice(self, email: str | None, value: str = "20.00",
                       currency: str = "USD", item_name: str = "audit probe item",
                       note: str | None = None, **kw) -> tuple[int, Any, dict]:
        # NOTE(spike-verified 2026-11-06): v2 create_invoice names the item array
        # "items" (NOT "line_items"). Unrecognized keys are SILENTLY dropped:
        # a body with line_items produced a valid-looking invoice whose
        # wire amount/due were 0.00 (spike3g/3h receipts).
        body: dict = {
            "detail": {"currency_code": currency},
            "items": [{
                "name": item_name,
                "unit_amount": {"currency_code": currency, "value": value},
                "quantity": "1",
            }],
        }
        if note is not None:
            body["detail"]["note"] = note
        if email:
            body["primary_recipients"] = [{"billing_info": {"email_address": email}}]
        status, resp, meta = self.call("POST", "/v2/invoicing/invoices", json=body, **kw)
        # convenience: surface the embedded id (self-link) as body["id"]
        if isinstance(resp, dict) and not resp.get("id"):
            m = re.search(r"v2/invoicing/invoices/([A-Za-z0-9\-]+)", json.dumps(resp))
            if m:
                resp = {**resp, "id": m.group(1)}
        return status, resp, meta

    def send_invoice(self, invoice_id: str, email: str, **kw) -> tuple[int, Any, dict]:
        return self.call("POST", f"/v2/invoicing/invoices/{invoice_id}/send",
                         json={"send_to_recipient": True,
                               "send_invoices": [{"invoice_recipient": email}]}, **kw)

    def get_invoice(self, invoice_id: str, **kw) -> tuple[int, Any, dict]:
        return self.call("GET", f"/v2/invoicing/invoices/{invoice_id}", **kw)

    def record_payment(self, invoice_id: str, value: str = "5.00",
                       currency: str = "USD", method: str = "CASH",
                       note: str | None = None, payment_date: str | None = None, **kw) -> tuple[int, Any, dict]:
        body: dict = {
            "method": method,
            "amount": {"currency_code": currency, "value": value},
        }
        if note is not None:
            body["note"] = note
        body["payment_date"] = payment_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.call("POST", f"/v2/invoicing/invoices/{invoice_id}/payments",
                         json=body, **kw)


    def record_refund(self, invoice_id: str, value: str = "2.00",
                      currency: str = "USD", method: str = "CASH", **kw) -> tuple[int, Any, dict]:
        # NOTE(spike-verified 2026-11-06): /refunds requires a "method" field
        # (400 MISSING_REQUIRED_PARAMETER /method without it).
        return self.call("POST", f"/v2/invoicing/invoices/{invoice_id}/refunds",
                         json={"amount": {"currency_code": currency, "value": value},
                               "method": method}, **kw)


def json_dumps(payload: dict) -> str:
    import json
    return json.dumps(payload, separators=(",", ":"))
