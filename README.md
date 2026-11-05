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

Status: **spike day 2026-11-06** - invoice family verified end-to-end on the
sandbox (create -> record_payment -> record_refund); order money path closed
on the default payee; headline finding SF-5 (silent drop -> $0 invoice) is
receipted in `runs/` and catalogued in `docs/evidence.md`. Harness next.

## What AI does (and does not do)

* compile natural-language merchant policy -> schema-validated DSL (human confirms),
* explain counterexamples and propose policy repairs, **re-verified by the
  deterministic checker** - the checker decides, not the LLM,
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
.venv\Scripts\python scripts\spike0_smoke.py            # credentials + reads
.venv\Scripts\python scripts\spike1_dup_probe.py        # idempotency ground truth
.venv\Scripts\python scripts\spike2_money_path.py       # card capture gate (needs test card in .env)
.venv\Scripts\python scripts\spike3_invoice_roundtrip.py# invoice fallback slice
.venv\Scripts\python scripts\spike4_mcp_snapshot.py     # MCP tool list (+ --remote)
```

Every run leaves receipts in `runs/` (git-ignored); sanitized, committed
evidence goes in `atlas/` once the harness pass starts.

## Repo layout

```
asa/            harness + matrix + clients (packages out of probe.py next)
  config.py     production guard + env
  matrix.py     108-cell definition, prune rules, tool targets
  recorder.py   JSONL receipts
  rest_client.py sandbox REST + PayPal-Request-Id hooks
  mcp_client.py stdio/HTTP MCP wrappers (official `mcp` SDK)
scripts/        spike0-4 - every spike FAIL is a pre-decided fallback
policies/       policy DSL schema v0 + the demo policy
docs/           evidence ledger (tagged), execution plan
atlas/          (after harness pass) doc-vs-sandbox delta tables, receipts
```

## Rules compliance snapshot (detail in docs/plan.md)

* newly created work, sandbox only, sole-owner check pending (contract review),
* public repo + MIT licence at repo top, run instructions for judges,
* video < 3 min on YouTube, no third-party music/trademarks,
* targets lanes: Best Use of PayPal + AI, Best Demo Delivery.

## Licence

MIT - see `LICENSE`.
