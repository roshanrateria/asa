# Evidence ledger (updated 2026-11-06)

Carried from the ideation report (2026-11-01). Items re-verified in session are
tagged `V-1105` / `V-1106` by the day they were checked. Unknowns stay explicit.

## Verified this week (fresh fetches)

1. **Deadline.** Thu 12 Nov 2026, 12:00 pm PT (PST - DST ended Nov 1) = 20:00 UTC
   = Fri 13 Nov ~01:30 IST. Judging Dec 1-15; winners on/around Dec 21. [V-1106, devpost rules + dates pages]
2. **Functional demo rule wording.** Setup-and-run instructions in the repo *or*
   a hosted demo URL; judges are not required to run the project but must "be
   able to actually run or interact with a working build"; a mockup or
   non-functional demo does not qualify. [V-1106, rules §4]
3. **Repo + video.** Public repo with a detectable open-source licence visible at
   the top of the repo; YouTube video < 3 min, public, showing the project
   functioning on the device it was built for, no third-party trademarks or
   copyrighted music without permission. [V-1106]
4. **Stale-project rule.** Existing projects must be significantly updated after
   the submission period opened; entrants explain how. asa is newly created
   (git history will show it), so this clause is satisfied trivially. [V-1106]
5. **Prizes.** $67,500 on the Devpost pages; one Devpost update says $69,750
   (discrepancy noted, rules §8 prevails). Categories seen: 1st/2nd/3rd ($12k/$8k/$5k),
   Most Creative, Most Impactful, Best Demo Delivery, Best Use of PayPal + AI,
   Best Use of Agentic Commerce, plus sponsor tiers (AG Grid x3, APIMatic,
   Bryntum, Channel3, Render credits x3, ...). ~29.0-29.3k participants. [V-1106]
6. **Agent-toolkit tool list (correction to ledger #11).** The toolkit README
   lists the full invoice family: create_invoice, list_invoices, get_invoice,
   send_invoice, send_invoice_reminder, cancel_sent_invoice, delete_invoice,
   generate_invoice_number, search_invoicing, update_invoicing,
   record_payment_for_invoice, record_refund_for_invoice, recurring-series set,
   conditional rules; payments: create_order, get_order, pay_order, create_refund,
   get_refund; disputes: list/get/accept_dispute_claim; reporting:
   list_transactions, get_merchant_insights. E6's slice tool names all exist. [V-1106, github.com/paypal/agent-toolkit README]
7. **MCP endpoints.** Sandbox: https://mcp.sandbox.paypal.com (transports /sse and
   /http). Production mcp.paypal.com (out of scope). Local stdio: npx -y @paypal/mcp
   --tools=all with PAYPAL_ACCESS_TOKEN + PAYPAL_ENVIRONMENT=SANDBOX; tokens valid
   3-8 h. Remote supports mcp-remote with OAuth login flow, or a Bearer header
   (--header "Authorization: Bearer <token>"). [V-1105/1106, developer.paypal.com MCP quickstart]
8. **Sandbox mechanics (official getting-started guide).** Default Business +
   Personal sandbox accounts auto-created; more accounts createable with chosen
   country/currency; buyer approval for wallet payments is a www.sandbox.paypal.com
   sign-in action by the Personal account; test funds/currency editable per account.
   [V-1106, official sandbox guide]
9. **Negative testing affordance.** Any sandbox REST call may force an error with
   the PayPal-Mock-Response header (mock_application_codes; e.g. INSTRUMENT_DECLINED,
   DUPLICATE_INVOICE_ID which returns 422 UNPROCESSABLE_ENTITY); account-level
   negative toggle also exists in the dashboard. Sandbox-only, documented. [V-1106]
   - Implication: recorded receipts carry mock_header_used=true/false so forced
     and organic behaviour stays distinguishable in the atlas.
10. **Early-review tip expired.** Devpost update: "Submit by Thursday, Nov 5 and
    our review team will check your project for eligibility early." That was
    yesterday; passed. Mitigation: still create the draft submission early. [V-1106]

## Spike session findings (2026-11-06, receipts in runs/)

All findings have JSONL receipts with debug_ids. Frame: measurement on the
sandbox with our own credentials, n stated, never "bugs" - behaviour deltas.

| # | Finding | Evidence |
|---|---|---|
| SF-1 | **Idempotency enforcement is asymmetric on the same API.** Plain order create: no header -> two distinct orders (silent duplicate write), same header -> one id. Card-funded order create: `PayPal-Request-Id` is REQUIRED (`PAYPAL_REQUEST_ID_REQUIRED`, 400) - surfaced only via the error (not the reference). | spike1 (6 receipts) + spike2 receipts |
| SF-2 | **Order money path is closed on the default payee**: `PAYEE_NOT_ENABLED_FOR_CARD_PROCESSING` (422) for card capture, two card variants tried; wallet capture needs the sandbox.buyer UI. Expiry format empirically pinned: wire wants `YYYY-MM`; `MM/YYYY` 400s (loud rejection - contrast with SF-5). | spike2 receipts |
| SF-3 | **India-recipient geometry surfaces under wrong HTTP semantics**: send/record to the India-country Personal sandbox account -> 406 MEDIA_TYPE_NOT_ACCEPTABLE wrapping `INR_FOREIGN_CURRENCY_BLOCKED` (business rule in a content-negotiation status). Send to a recipient outside India (RFC-2606 example.com) works normally. | spike3 v1 vs spike3d receipts |
| SF-4 | **Refund-method enum is undocumented-narrow**: refund method CARD and EXTERNAL -> 400 `INVALID_REFUND_METHOD` at schema level; CASH/BANK_TRANSFER/PAYPAL accepted into the invariant check. That's 2 of 5 accepted-method observations disagreeing with doc enumeration. | spike3c receipts (8) |
| SF-5 | **Silent drop of a mis-keyed money field at creation - THE headline finding.** create_invoice with `line_items` (wrong key; ex-graphics uses `items`): 201 Created, valid-looking object, but wire amount/due = **0.00**. A $20 invoice stored as a $0 object, no schema error anywhere. Downstream: record_payment accepted-with-200 stores amount 0.00 (paid_amount 0.00) while the invoice flips MARKED_AS_PAID; every record_refund (n=13 across states/methods/headers/amounts) 422s INVALID_REFUND_AMOUNT - arithmetically true against a zero payment, message contradicts the invoice's own state. | spike3b/3c/3d/3e/3f/3g/3h receipts |
| SF-6 | **With the correct `items` key the family is fully live**: due 20.00 on wire; record_payment ({"method","amount","payment_date","note"}) stores 5.00 -> PARTIALLY_PAID; record_refund 2.00 -> **200** (PARTIALLY_PAID final). Harness helpers verified end-to-end through the same route (spike3j). Tonight's SF-5 chain re-tags: refund engine fine; the corruption is the silent drop at creation. | spike3i + spike3j receipts |
| SF-7 | Default sandbox app lacks Transaction Search scope: list_transactions 403 NOT_AUTHORIZED while list_invoices 200 - docs-expose-it vs sandbox-app-can't-run-it delta. | spike0 receipts |
| SF-8 | **MCP surface is narrower than the toolkit's.** stdio snapshot: 28 tools; `record_payment_for_invoice` and `record_refund_for_invoice` are NOT exposed as MCP tools (refund only via create_refund against a captured payment). An agent driven through PayPal's own MCP server cannot perform the invoicing money lifecycle that the toolkit advertises. Snapshot artifact: runs/mcp_tools_snapshot_stdio.json. | spike4 receipts |

Receipt tally today: ~80 lines across 17 runs (spike0-3j), all in runs/, all
fresh sandbox objects (orders/invoices left in place; nothing destructive).

### Unknowns resolved or narrowed
* **B (PayPal-Request-Id in practice)**: REST-side semantics confirmed (SF-1).
  MCP-server-side mirror still open (needs spike4 run once node/token set up).
* **C (Orders v2 card shape)**: shape accepted structurally; blocker moved to
  the payee gate (SF-2). Keep card path closed for MVP.
* **NEW state**: refunds DO work once due > 0 - matrix REFUND cells are live
  for the invoice family.

### Corrections to earlier ledger items
* #15's India sandbox limitation (old forum report) now has a current primary
  observation (SF-3), recipient-side, with a status-code mismatch twist.

## Carried verified (from 2026-11-01 report, not re-fetched)

11. Stage One pass/fail on theme fit + required-API use; Stage Two five equally
    weighted criteria; AI-assisted judging permitted; original and solely-owned
    work; exclusion list does not name India. [V-1101]
12. PayPal-Request-Id idempotency semantics; omitting it can duplicate requests. [V-1101]
13. Dev Days 2025 winners n=3 (CrawlerPal, Codebusters, Rosen). [V-1101]

## Corrections vs the 2026-11-01 report

* Ledger #11's tool list was incomplete - the invoice family does include
  create_invoice/send_invoice/get_invoice, so E6's MVP slice is defensible as written.
* E8 risk 1 (no programmatic capture) is now sharper: wallet capture definitely
  needs buyer UI; viable programmatic money paths are (a) card payment_source
  capture with test-card data, (b) invoice record_payment/record_refund.

## Open unknowns (U) - each with its resolution path

A. **Sandbox rate limits** - unknown. Resolution: probe harness paces itself;
   coverage reported against attempted, not promised, cells.
B. **Does the toolkit/MCP server send PayPal-Request-Id?** - script
   `scripts/spike1_dup_probe.py` settles the REST side; MCP-side mirrors after spike 4.
C. **Exact Orders v2 payment_source.card body shape** - confirm live in spike 2;
   rejection is recorded and the card path is dropped for the invoice fallback.
D. **Programmatic dispute creation in sandbox** - unverified; disputing probes
   stay out of the MVP (stretch only), per E6.
E. **Remote MCP bearer-header auth via direct SDK** - attempted in spike 4
   (--remote); stdio fallback documented.
F. **Sponsor tool terms / docs (APIMatic, Kernel, etc.)** - not opened; not needed
   for P; only relevant if a sponsor lane is ever targeted.

## Protocol shortfalls (still standing)

* R3: fewer than 6 primary prior-art items per theme; new queries scheduled for
  the harness weekend.
* Patent search: not done.
* Past-winner depth: n=3 only.
