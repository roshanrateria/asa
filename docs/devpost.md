# Devpost submission text (review-vetted draft, freeze 2026-11-10)

## Title

Agent Surface Audit (asa) - measure PayPal's agent surface, compile merchant
policies from receipts, document the carried hazards

## Elevator (~300 chars)

asa is a black-box audit of PayPal's own agent surface: the official MCP
server and the REST invoice family, probed with a 108-candidate matrix on the
sandbox (96 excluded with a receipted reason each; 51 REST + 12 MCP executed
in the canonical run). Every call leaves a receipt. An LLM compiles merchant
policies into a small DSL from the docs, a deterministic checker confronts
the compiled policy with the receipts, and the carried hazards end up
explicitly documented - receipts arbitrate, not vibes.

## What it does

* probes 4 abuse classes over PayPal's money endpoints (duplicate retries,
  illegal states, cumulative over-limit sequences, untrusted echoes) across
  REST and the official MCP server (version-pinned @paypal/mcp@1.8.1,
  --tools=all snapshot);
* labels every cell PASS / DRIFT / OBSERVE against the documented contract,
  and *never* claims more than its JSONL receipts;
* compiles merchant policies into `policies/compiled/*.json`: the v0
  doc-faithful variants FAIL with receipted counterexamples; the v1 files
  are explicitly `policy_status: known-hazard documentation` - scope
  narrowed to receipted truth with the merchant-side mitigation written out
  (the fail -> hazard-documentation cycle is the demo);
* attaches AI to the headline masking finding and MEASURES it: same masked
  tool text + the real create_invoice schema, NVIDIA primary model n=20/cell
  (temp 0.7) + glm-5.3-flash-free cross-engine legs n=5/cell, counts with
  Wilson intervals - 0 hazard outcomes in 75 measured trials; the exposure
  NOT yet demonstrated is a client that forwards only the structured flag
  (stated as hypothesis, not result);
* replays the headline findings live (`scripts/replay_findings.py`) so judges
  see today's sandbox, not Day-one claims;
* renders ONE offline static report (`report/index.html`) built only from
  receipt-derived JSON artifacts.

## Receipt-based findings (sample)

* SF-1: idempotency is asymmetric - orders v2 honors PayPal-Request-Id
  (return-existing ~49 min later); the invoicing create/payments/refunds
  endpoints ignore it, so same-header retries duplicate money objects.
* SF-5 (the headline, REST-family): create_invoice silently accepts the WRONG
  field key (`line_items`), returns 201 with a completely valid-looking object
  whose amount/due are 0.00 - a $20 invoice stored as a $0 object with no
  error anywhere; refunds then 422 with a message contradicting the object's
  own state. Scope receipted: the MCP tool's schema ENFORCES `items`
  (`-32602 Required at items`), so agents on MCP cannot mis-key their way to
  a $0 invoice - the hazard is REST-only.
* SF-8: the official MCP server cannot record invoices payments/refunds - the
  toolkit advertises the tools, the server does not expose them.
* SF-9: MCP reports `isError=false` while its result TEXT carries the
  application-level failure (`{"ok":false,"status":406}`). Measured with AI
  attached: the agents SHOWN the text catch it in 0 hazards / 75 measured
  trials (NVIDIA n=20/cell + GLM cross-engine n=5/cell, Wilson intervals in
  `atlas/agent_probe.json`); the exposure NOT demonstrated (labeled
  hypothesis, not result) is a client that forwards only the structured flag. Second
  independent instance receipted: a create_invoice schema rejection
  (`-32602 Required at items`) also rides `isError=false` with the error
  only in text (`atlas/miskey_mcp_check.json`).
* SF-10: identical hostile `<script>` text is rejected with THREE different
  artifacts (406+empty body / 403+WAF HTML page / masked-406-in-text), while
  prompt-injection text passes everywhere and is stored verbatim.
  (Labeled OBSERVE: a WAF block on `<script>` is expected hardening - the
  measurement documents the split's unpredictability, not a doc delta.)

Full ledger: `docs/evidence.md` (SF-1..SF-10), atlas `atlas/atlas_v0.*`.
Version pin: tool-surface claims are made against `@paypal/mcp@1.8.1`
(package spec + spawn args + date recorded in the snapshot's provenance
block).

## Why "Best Use of PayPal + AI"

The audit runs exclusively through PayPal's own official surfaces (the
@paypal/mcp stdio server + sandbox REST) - PayPal's resources ARE the object
under test. AI is named, load-bearing, and bounded: GLM-5.3 Flash Free (via
the opencode harness; transcripts at `docs/llm_transcripts.md` - prompts,
raw compiled outputs, checker console) compiled the policies and drafted the
hazard-documentation repairs, but the deterministic receipt-checker
(`asa/policy.py`) decides every verdict; the artifact chain (compile ->
fail -> counterexamples -> documented-hazard v1 -> recheck) is inspectable
file by file. The measured agent result (0 hazards in 75 trials, NVIDIA
n=20/cell + GLM legs, Wilson intervals) is the AI-story with numbers
underneath. Sandbox-only BY CONSTRUCTION (`asa/config.py`
hard-refuses any non-sandbox credential; receipts carry a mock-header flag so
forced and organic behavior stay distinguishable).

## Judges can run it

```powershell
cp .env.example .env   # paste YOUR sandbox client id/secret
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\replay_findings.py   # ~7 bounded sandbox calls, prints 4/4 REPLAYED
.venv\Scripts\python scripts\agent_probe.py       # NVIDIA leg (add free NVIDIA_API_KEY); then scripts\merge_probe_harness.py for cross-engine legs
.venv\Scripts\python scripts\build_report.py      # renders report\index.html from artifacts
```

Committed artifacts let judges audit without running anything: the sanitized
subset `atlas/sample_receipts/` (receipts: masked failure, header
pairs, replay rows, pinned tool list; scrubbed by
`scripts/build_sample_receipts.py`), the policy chain, `report/index.html`.
Git history is secret-scanned: `.env` was never committed; the only
pickaxe hit for `client_secret` is the env-var NAME in `.env.example`.

## Built with

Python 3.13 (httpx, mcp official SDK) | @paypal/mcp stdio server | PayPal
Sandbox REST v1/v2 | JSONL receipt format v1 | git + a laptop.

## Notes

* All findings are behaviour deltas of the SANDBOX surface (n procedurally
  receipted); none claim production behavior.
* No mock headers anywhere in the harness receipts (mock_header_used=false
  throughout) - the negative testing affordance stays scope-out and honest.
* Human role: every v1 artifact is human-reviewed before it lands; the
  checker owns verdicts; the LLM's usage is bounded and named
  (see `docs/llm_transcripts.md`).
* All findings version-pinned to @paypal/mcp@1.8.1 where tool surfaces matter.
