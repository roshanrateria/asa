# Devpost submission text (draft, freeze 2026-11-08)

## Title

Agent Surface Audit (asa) - measure PayPal's agent surface, compile & repair
merchant policies from receipts

## Elevator (~300 chars)

asa is a black-box audit of PayPal's own agent surface: the official MCP
server and the REST invoice family, probed with a 108-cell matrix on the
sandbox. Every call leaves a receipt. An LLM compiles merchant policies into
a small DSL from the docs, a deterministic checker confronts the compiled
policy with the receipts, and the repair loop re-scope the policy to what the
sandbox actually does - receipts arbitrate, not vibes.

## What it does

* probes 4 abuse classes over PayPal's money endpoints (duplicate retries,
  illegal states, cumulative over-limit sequences, untrusted echoes) across
  REST and the official MCP server;
* labels every cell PASS / DRIFT / OBSERVE against the documented contract,
  and *never* claims more than its JSONL receipts;
* compiles merchant policies into `policies/compiled/*.json`: the v0
  doc-faithful variants FAIL with receipted counterexamples; the v1 repairs
  are scope-shrunk to receipted behavior (the fail->repair cycle is the demo);
* replays the headline findings live (`scripts/replay_findings.py`) so judges
  see today's sandbox, not Day-one claims;
* renders ONE offline static report (`report/index.html`) built only from
  receipt-derived JSON artifacts.

## Receipt-based findings (sample)

* SF-1: idempotency is asymmetric - orders v2 honors PayPal-Request-Id
  (return-existing ~49 min later); the invoicing create/payments/refunds
  endpoints ignore it, so same-header retries duplicate money objects.
* SF-5 (the headline): create_invoice silently accepts the WRONG field key
  (`line_items`), returns 201 with a completely valid-looking object whose
  amount/due are 0.00 - a $20 invoice stored as a $0 object with no error
  anywhere; refunds then 422 with a message contradicting the object's own
  state.
* SF-8: the official MCP server cannot record invoices payments/refunds - the
  toolkit advertises the tools, the server does not expose them.
* SF-9: MCP reports `isError=false` while its result TEXT carries the
  application-level failure (`{"ok":false,"status":406}`) - an agent reading
  structured flags acts on a failed call.
* SF-10: identical hostile `<script>` text is rejected with THREE different
  artifacts (406+empty body / 403+WAF HTML page / masked-406-in-text), while
  prompt-injection text passes everywhere and is stored verbatim.

Full ledger: `docs/evidence.md` (SF-1..SF-10), atlas `atlas/atlas_v0.*`.

## Why "Best Use of PayPal + AI"

The audit runs exclusively through PayPal's own official surfaces (the
@paypal/mcp stdio server + sandbox REST) - PayPal's resources ARE the object
under test. AI is load-bearing in the documented place: the LLM compiles
policies and drafts repairs, but a deterministic receipt-checker decides
every verdict; the artifact chain (compile -> fail -> repair -> recheck) is
inspectable file by file. Sandbox-only BY CONSTRUCTION (`asa/config.py`
hard-refuses any non-sandbox credential; receipts carry a mock-header flag so
forced and organic behavior stay distinguishable).

## Judges can run it

```powershell
cp .env.example .env   # paste YOUR sandbox client id/secret
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\replay_findings.py   # ~6 bounded sandbox calls, prints REPLAYED
.venv\Scripts\python scripts\build_report.py      # renders report\index.html from artifacts
```

Committed artifacts (`atlas/`, `runs/` receipts referenced inside, policy
chain, `report/index.html`) let judges audit without running anything.

## Built with

Python 3.13 (httpx, mcp official SDK) | @paypal/mcp stdio server | PayPal
Sandbox REST v1/v2 | JSONL receipt format v1 | git + a laptop.

## Notes

* All findings are behaviour deltas of the SANDBOX surface (n procedurally
  receipted); none claim production behavior.
* No mock headers anywhere in the harness receipts (mock_header_used=false
  throughout) - the negative testing affordance stays scope-out and honest.
* Human role: every policy repair is reviewed before it lands; the checker
  owns verdicts.
