# Agent Surface Audit (`asa`)

Black-box audit of **PayPal's own agent surface** - the official Agent Toolkit
and MCP server - measured against their **sandbox** behaviour, then bounded
exploit-sequence search over the measured model, with an LLM compiling
merchant policies into a small DSL.

Built for the PayPal AI Hackathon ("Build What's Next with PayPal and AI",
deadline Thu 12 Nov 2026, 12:00 PST). Sandbox only, by construction.

## Why

Merchants are handing agents refund and payment powers. The existing answers
are runtime guards (policy proxies) or generic verifiers. What nobody has
published, to our knowledge as of 2026-11-01, is a **measured behaviour model**
of PayPal's own agent tools on the sandbox: what a duplicate call actually
does, which illegal states are actually accepted, how a cumulative
over-limit sequence behaves, what untrusted text through supported fields
does. asa probes first with receipts on every call, and never enforces at
runtime - it is an audit tool for teams before they ship agents.

Status: **harness live over the invoice anchor**. Spike day verified the
invoice family end-to-end (create -> record_payment -> record_refund) and
catalogued SF-1..SF-8 with receipts; the 108-cell matrix then ran to a
receipt-clean canonical pass (PASS / DRIFT / OBSERVE, artefacts under
`atlas/`), adding SF-9 (MCP masks application failure as success) and
SF-10 (hostile-text handling splits across artifacts). Headline finding
SF-5 (silent drop -> $0 invoice) is replayable live via
`scripts/replay_findings.py`.

## What AI does (and does not do)

* compile natural-language merchant policy -> schema-validated DSL
  (compiled v0 artifacts under `policies/compiled/`, human-confirmable),
* explain counterexamples and propose policy repairs - then a
  **deterministic checker re-verifies** against receipts: the checker decides,
  not the LLM (see `scripts/policy_check.py` and the `*_v1.json` repairs),
* (stretch) agent replay across 2-3 models.

## Architecture (blueprint E5)

```
targets:    REST api-m.sandbox.paypal.com | MCP @paypal/mcp (stdio) |
            MCP mcp.sandbox.paypal.com/http (bearer-header attempt)
probes:     108-cell matrix = 4 abuse classes x 27 cells
            (3 effects x 3 preconditions x 3 call shapes), pruned + reported
recorder:   JSONL receipts per call (ids, debug_id, mock-header flag, ts)
model:      abstract states (order draft/authorized/captured; invoice
            draft/sent/paid/refunded; dispute open)
search:     explicit-state BFS, depth <= 6, amounts bucketed
report:     static HTML with before/after, replay ids, coverage stats
```

## Quickstart

Needs Python 3.11+. Node 18+ only for the MCP stdio spike.

```powershell
cp .env.example .env        # fill PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET (sandbox)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# probes (receipts land in runs\, git-ignored)
.venv\Scripts\python scripts\spike0_smoke.py              # credentials + reads
.venv\Scripts\python scripts\spike1_dup_probe.py          # idempotency ground truth
.venv\Scripts\python scripts\spike2_money_path.py         # card capture gate (needs test card in .env)
.venv\Scripts\python scripts\spike3_invoice_roundtrip.py  # invoice fallback slice
.venv\Scripts\python scripts\spike4_mcp_snapshot.py       # MCP tool list (+ --remote)

# the audit itself
.venv\Scripts\python scripts\harness_pass1.py --tag pass1d2   # 108-cell matrix (REST + MCP)
.venv\Scripts\python scripts\policy_check.py --canon pass1d2  # policy/v0 fails -> v1 repairs
.venv\Scripts\python scripts\replay_findings.py               # headline findings, live
.venv\Scripts\python scripts\build_atlas.py --canonical pass1d2  # delta tables
.venv\Scripts\python scripts\build_report.py                  # report\index.html (offline)
```

Judges: open `report/index.html` - it renders only what `runs/` receipts
prove, plus `atlas/atlas_v0.md` (same data, markdown form), with the
compiled-policy repair chain (`policies/compiled/*_v0.json` -> `*_v1.json`).

## Repo layout

```
asa/            matrix, ledger (per-cell per-transport rows), policy engine
  config.py     production guard + env (hard sandbox gate)
  matrix.py     108-cell definition, prune rules, tool targets
  recorder.py   JSONL receipts + id extraction
  rest_client.py sandbox REST + PayPal-Request-Id hooks
  mcp_client.py stdio MCP session (official `mcp` SDK)
  probe.py      matrix runner: anchor setups, retry shapes, verdicts
  policy.py     DSL v0 engine: compiled policies vs receipted canon
scripts/        spikes 0-4, harness, fx, atlas/report builders, replay
policies/       compiled policy artifacts (v0 doc-faithful -> v1 receipt-repaired)
docs/           evidence ledger (tagged), execution plan, submission text
atlas/          coverage passes + doc-vs-sandbox delta atlas + artifact JSONs
```

## Rules compliance snapshot (detail in docs/plan.md)

* newly created work, sandbox only, sole-owner check pending (contract review),
* public repo + MIT licence at repo top, run instructions for judges,
* video < 3 min on YouTube, no third-party music/trademarks,
* targets lanes: Best Use of PayPal + AI, Best Demo Delivery.

## Licence

MIT - see `LICENSE`.
