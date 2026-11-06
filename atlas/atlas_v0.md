# asa atlas v0 - doc-vs-sandbox deltas (auto-built from receipts)

canon: `pass1d2`
lineage kept: pass1, pass1b, pass1c (pass1's retry-verb plumbing bug is part of the audit trail)

verdict semantics: **PASS** = sandbox matches the documented/toolkit hypothesis; **DRIFT** = sandbox contradicts it (delta); **OBSERVE** = no verified hypothesis, measurement recorded.

## Coverage (canon + aux)

`{"total_cells": 108, "scheduled_rest": 51, "executed_rest": 51, "scheduled_mcp": 12, "executed_mcp": 12, "not_scheduled": {"single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only)": 54, "echo-refund: refund body has no text field on REST": 3, "mcp-shape-merge: one aggregate retry per cluster": 6, "mcp-tool-absent: SF-8 (record/refund not exposed by MCP)": 33}, "verdicts": {"PASS": 29, "DRIFT": 10, "OBSERVE": 24}}`

## Verdict pivot by transport (executed rows)

| transport | PASS | DRIFT | OBSERVE |
|---|---|---|---|
| mcp-stdio | 9 | 3 | 0 |
| rest | 20 | 7 | 24 |

## Doc-vs-sandbox deltas

| id | documented expectation | observed on sandbox | status | cites |
|---|---|---|---|---|
| D-1 | Retries carrying the same PayPal-Request-Id do not duplicate effects (docs: request-id idempotency, ledger #12). | orders v2 honors it - 201 then 200-return-existing with the SAME order id, still true ~49 min later. The invoicing family ignores it on every endpoint: same-header create pairs -> two distinct INV2 invoices [201,201] x3 flavor; same-header payments/refunds -> two distinct EXTR records [200,200]. | CONFIRMED-DELTA (3 of 4 money endpoints unidempotent) | spike1 12 receipts (2 runs); atlas cells 002/005/008 + 011/014/017-026; smoke-retry-shapes receipts |
| D-2 | Invoice create validates its money fields (docs: schema'd items/line_items). | 201 Created, visually valid object - but wire amount/due = 0.00. Money silently zeroed; downstream refunds then 422 INVALID_REFUND_AMOUNT against the object's own MARKED_AS_PAID state. | CONFIRMED-DELTA (silent schema lenience) | spike3g/3h/3b-3f receipts; SF-5 chain |
| D-3 | The toolkit advertises the full invoice money lifecycle (record_payment_for_invoice / record_refund_for_invoice). | 28 tools via stdio; the two record_* tools are absent, so an agent on PayPal's own MCP server cannot record payments/refunds on invoices - the lifecycle stops at create/send. | CONFIRMED-DELTA (surface narrower than advertised) | runs/mcp_tools_snapshot_stdio.json; harness mcp-tool-absent bucket (33 cells); SF-8 |
| D-4 | A tool call reports its failure through the structured error flag (MCP isError). | isError=false; the failure exists only inside result TEXT ({"ok":false,"status":406,"code":"PAYPAL_API_HTTP_ERROR","message":"Unknown error"}) - structured success lies about application failure. | CONFIRMED-DELTA (success flag masks failure) | harness pass1b seq 189/196; pass1c seq 183/190; SF-9 |
| D-5 | Input validation rejects hostile text with a debuggable API error. | script payload: block status/artifact splits across runs (406+empty body in pass1; 403+WAF HTML page in pass1b/1c) - see Echo matrix below. prompt payload: accepted everywhere, stored VERBATIM (echo=reflected-verbatim). | CONFIRMED-DELTA (three artifacts, no machine-readable rejection) | runs/harness-pass1{.jsonl,b,c} cells 082/088/094; echo rows 085/091/097; SF-10 |
| D-6 | Geo/currency business rules surface as 4xx app errors (send to India-recipient personal sandbox). | 406 MEDIA_TYPE_NOT_ACCEPTABLE with an EMPTY body wrapping the business rule - a content-negotiation status carrying a currency policy. | CONFIRMED-DELTA (wrong HTTP semantics for a business rule) | spike3 v1 vs spike3d receipts; SF-3 |
| D-7 | Refund method enum is as documented. | CARD and EXTERNAL -> 400 INVALID_REFUND_METHOD; 2 of 5 documented-enumeration methods disagree with the wire. | CONFIRMED-DELTA (enum narrower than docs) | spike3e receipts; SF-4 |
| D-8 | PayPal-Mock-Response negative testing works on invocations. | n/a - documented affordance, left for a later seeded rerun. | NOT EXERCISED (scope v0, honest exclusion) | - |

## Not-scheduled reasons (honest exclusions, never silence)

- ` 54` cells - single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only)
- `  3` cells - echo-refund: refund body has no text field on REST
- `  6` cells - mcp-shape-merge: one aggregate retry per cluster
- ` 33` cells - mcp-tool-absent: SF-8 (record/refund not exposed by MCP)

## Echo matrix (hostile-text artifact across passes)

| pass | cell | channel | status | artifact |
|---|---|---|---|---|
| pass1d2 | 82 | rest | 403 | waf-html-page |
| pass1d2 | 88 | rest | 403 | waf-html-page |
| pass1d2 | 94 | rest | 403 | waf-html-page |
| pass1d2 | 82 | mcp-stdio | 200 | masked-ok:false-text |
| pass1d2 | 88 | mcp-stdio | 200 | masked-ok:false-text |
| pass1 | 82 | rest | 406 | empty-body |
| pass1 | 88 | rest | 406 | empty-body |
| pass1 | 94 | rest | 406 | empty-body |
| pass1 | 82 | mcp-stdio | 200 | masked-ok:false-text |
| pass1 | 88 | mcp-stdio | 200 | masked-ok:false-text |
| pass1b | 82 | rest | 403 | waf-html-page |
| pass1b | 88 | rest | 403 | waf-html-page |
| pass1b | 94 | rest | 403 | waf-html-page |
| pass1b | 82 | mcp-stdio | 200 | masked-ok:false-text |
| pass1b | 88 | mcp-stdio | 200 | masked-ok:false-text |
| pass1c | 82 | rest | 403 | waf-html-page |
| pass1c | 88 | rest | 403 | waf-html-page |
| pass1c | 94 | rest | 403 | waf-html-page |
| pass1c | 82 | mcp-stdio | 200 | masked-ok:false-text |
| pass1c | 88 | mcp-stdio | 200 | masked-ok:false-text |

## Same-semantic surface table (REST vs MCP, executed rows)

| transport | executed | notes |
|---|---|---|
| rest (invoicing endpoints) | 51 | CREATE POST /v2/invoicing/invoices; RECORD POST /v2/invoicing/invoices/{id}/payments; REFUND POST /v2/invoicing/invoices/{id}/refunds |
| mcp-stdio (@paypal/mcp) | 12 | CREATE create_invoice only; RECORD/REFUND absent (D-3); result text masks failure (D-4) |

## Findings index (from docs/evidence.md)

SF-1 cross-endpoint idempotency asymmetry; SF-2 order card path payee-gated; SF-3 406-wrapped geo rule; SF-4 refund enum narrow; SF-5 silent line_items drop -> $0 invoice; SF-6 items-key family fully live; SF-7 transactions scope missing; SF-8 MCP record/refund absent; SF-9 MCP masked failure; SF-10 hostile-text artifact split.

## Reproducibility

```
python scripts\harness_pass1.py --tag <tag>   # full matrix
python scripts\fx_cells.py --tag <tag>-fx --cells <ids>  # failed-cell follow-up
python scripts\smoke_retry_shapes.py          # retry-shape plumbing proof
python scripts\forensics_cross.py             # cross-pass echo/status forensics
python scripts\build_atlas.py --canonical <tag> --aux <tag>-fx
```

