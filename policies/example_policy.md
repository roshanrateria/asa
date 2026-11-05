# Demo policy (E9 script) and its compiled DSL

Natural language, as a merchant would hand to their agent:

> "The agent may record payments and issue refunds on my invoices.
> Each refund is capped at $50.00 USD, and total refunds per invoice
> must not exceed $50.00 USD. Never touch an invoice that has an
> open dispute."

Compiled DSL (`asa://policy/v0`, schema at `policies/policy.schema.json`):

```json
{
  "name": "demo-refund-cap-50",
  "currency": "USD",
  "refund": {
    "per_refund_max": "50.00",
    "total_refund_max": "50.00",
    "total_scope": "per_invoice",
    "forbid_after": ["dispute_open"]
  }
}
```

Lifecycle notes:
* compiled by the LLM, schema-validated, then human-confirmed before search runs;
* counterexample explanations and repair proposals go through the same
  compile step and are re-verified by the deterministic checker - the checker
  decides, the LLM only proposes;
* the cumulative-cap search targets `total_refund_max` via many small legal
  record_refund_for_invoice calls (abuse class CUMULATIVE_OVERLIMIT).

_(demo-script rule: no counterexample trace is shown anywhere until a spike-
confirmed replay exists; pre-spike material stays hypothetical and is marked
as such.)_
